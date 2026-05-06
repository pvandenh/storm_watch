"""Storm Watch DataUpdateCoordinator.

Calls weather.get_forecasts on the configured hourly and daily weather
entities, analyses each time window for storm risk, and exposes a single
alert level plus rich metadata for all sensor/binary_sensor platforms.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ALERT_EMERGENCY,
    ALERT_NONE,
    ALERT_WARNING,
    ALERT_WATCH,
    CONF_DAILY_ENTITY,
    CONF_HOURLY_ENTITY,
    CONF_PRECIP_EMERGENCY,
    CONF_SCAN_INTERVAL,
    CONF_SEVERE_CONDITIONS,
    CONF_STORM_CONDITIONS,
    CONF_WIND_EMERGENCY,
    CONF_WIND_WARNING,
    DEFAULT_PRECIP_EMERGENCY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SEVERE_CONDITIONS,
    DEFAULT_STORM_CONDITIONS,
    DEFAULT_WIND_EMERGENCY,
    DEFAULT_WIND_WARNING,
    DOMAIN,
    KEY_DETAIL,
    KEY_FORECASTS_DAILY,
    KEY_FORECASTS_HOURLY,
    KEY_HAZARDS,
    KEY_LEVEL,
    KEY_WINDOW,
    WINDOW_12H,
    WINDOW_1H,
    WINDOW_3H,
)

_LOGGER = logging.getLogger(__name__)


class StormWatchCoordinator(DataUpdateCoordinator):
    """Fetch forecasts and compute storm alert level on a schedule."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._hourly_entity: str = entry.data[CONF_HOURLY_ENTITY]
        self._daily_entity: str  = entry.data[CONF_DAILY_ENTITY]

        # Thresholds — fall back to defaults if not in config
        self._wind_emergency: float = float(entry.options.get(
            CONF_WIND_EMERGENCY, entry.data.get(CONF_WIND_EMERGENCY, DEFAULT_WIND_EMERGENCY)
        ))
        self._wind_warning: float = float(entry.options.get(
            CONF_WIND_WARNING, entry.data.get(CONF_WIND_WARNING, DEFAULT_WIND_WARNING)
        ))
        self._precip_emergency: float = float(entry.options.get(
            CONF_PRECIP_EMERGENCY, entry.data.get(CONF_PRECIP_EMERGENCY, DEFAULT_PRECIP_EMERGENCY)
        ))
        # Storm/severe condition lists are not exposed in the config flow yet;
        # they always resolve to the defaults defined in const.py.
        self._storm_conditions: list[str] = entry.options.get(
            CONF_STORM_CONDITIONS, entry.data.get(CONF_STORM_CONDITIONS, DEFAULT_STORM_CONDITIONS)
        )
        self._severe_conditions: list[str] = entry.options.get(
            CONF_SEVERE_CONDITIONS, entry.data.get(CONF_SEVERE_CONDITIONS, DEFAULT_SEVERE_CONDITIONS)
        )

        scan_minutes = int(entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_minutes),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch forecasts and compute alert level."""
        try:
            hourly_forecasts = await self._get_forecasts(self._hourly_entity, "hourly")
            daily_forecasts  = await self._get_forecasts(self._daily_entity,  "daily")
        except Exception as err:
            raise UpdateFailed(f"Failed to fetch forecasts: {err}") from err

        now = datetime.now(timezone.utc)
        level, window, hazards = self._analyse(now, hourly_forecasts, daily_forecasts)
        detail = self._build_detail(hazards)

        return {
            KEY_LEVEL:            level,
            KEY_WINDOW:           window,
            KEY_DETAIL:           detail,
            KEY_HAZARDS:          hazards,
            KEY_FORECASTS_HOURLY: hourly_forecasts,
            KEY_FORECASTS_DAILY:  daily_forecasts,
        }

    async def _get_forecasts(self, entity_id: str, forecast_type: str) -> list[dict]:
        """Call weather.get_forecasts service and return the forecast list."""
        response = await self.hass.services.async_call(
            WEATHER_DOMAIN,
            "get_forecasts",
            {"type": forecast_type},
            target={"entity_id": entity_id},
            blocking=True,
            return_response=True,
        )
        if not response:
            _LOGGER.warning("No response from weather.get_forecasts for %s", entity_id)
            return []
        # Response is keyed by entity_id
        entity_data = response.get(entity_id, {})
        return entity_data.get("forecast", [])

    def _parse_dt(self, dt_str: str) -> datetime | None:
        """Parse ISO8601 datetime string from forecast to UTC datetime."""
        if not dt_str:
            return None
        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError):
            return None

    def _analyse(
        self,
        now: datetime,
        hourly: list[dict],
        daily: list[dict],
    ) -> tuple[str, str, dict[str, bool]]:
        """
        Analyse forecast data and return (level, window_text, hazards_dict).

        Hazards dict contains boolean flags for each detected risk type,
        used by individual sensors to expose granular data.
        """
        all_storm = self._storm_conditions
        all_severe = self._severe_conditions + self._storm_conditions  # severe is superset

        cutoff_1h  = now + timedelta(seconds=WINDOW_1H)
        cutoff_3h  = now + timedelta(seconds=WINDOW_3H)
        # BOM's hourly feed typically covers ~48 h, so WINDOW_12H slots will
        # always be present. If you switch to a provider with a shorter hourly
        # range, h12_* flags may silently stay False — cross-check with daily.
        cutoff_12h = now + timedelta(seconds=WINDOW_12H)

        # ── Scan hourly slots ────────────────────────────────────────────────
        h1_storm  = h1_wind  = h1_rain  = False
        h3_storm  = h3_wind  = h3_severe = False
        h12_storm = h12_severe = False

        for slot in hourly:
            slot_dt = self._parse_dt(slot.get("datetime", ""))
            if slot_dt is None or slot_dt <= now:
                continue

            condition  = slot.get("condition", "")
            wind_speed = slot.get("wind_speed") or 0
            precip     = slot.get("precipitation") or 0

            is_storm  = condition in all_storm
            is_severe = condition in all_severe

            if slot_dt <= cutoff_1h:
                if is_storm:
                    h1_storm = True
                if wind_speed > self._wind_emergency:
                    h1_wind = True
                if precip > self._precip_emergency:
                    h1_rain = True

            if slot_dt <= cutoff_3h:
                if is_storm:
                    h3_storm = True
                if wind_speed > self._wind_warning:
                    h3_wind = True
                if is_severe:
                    h3_severe = True

            if slot_dt <= cutoff_12h:
                if is_storm:
                    h12_storm = True
                # For the 12 h window, require a threshold breach in addition to
                # a severe condition code. This prevents ambient "rainy" / "pouring"
                # slots (which BOM uses for ordinary showers) from raising h12_severe
                # when there is no meaningful wind or precipitation behind them.
                if is_severe and (
                    wind_speed > self._wind_warning
                    or precip > self._precip_emergency
                ):
                    h12_severe = True

        # ── Scan daily slots (skip today = index 0) ──────────────────────────
        if len(daily) < 2:
            _LOGGER.warning(
                "Daily forecast has fewer than 2 slots (%d); tomorrow storm check skipped",
                len(daily),
            )
        tomorrow_storm = False
        for slot in daily[1:2]:  # only check tomorrow (index 1), not the whole week
            condition = slot.get("condition", "")
            # Use all_storm (not all_severe) so that ordinary "rainy" / "pouring"
            # conditions — which BOM uses for routine showers — do not trigger a
            # "Storm Tomorrow" alert. The severe-condition set is intentionally
            # broad for the short hourly windows where wind/precip thresholds act
            # as a secondary filter, but daily slots carry no such numeric data so
            # we must restrict to unambiguous storm-class codes here.
            if condition in all_storm:
                tomorrow_storm = True

        # ── Determine level ──────────────────────────────────────────────────
        if h1_storm or (h1_wind and h1_rain):
            level  = ALERT_EMERGENCY
            window = "Within 1 hour"
        elif h3_storm or h3_wind or h3_severe:
            level  = ALERT_WARNING
            window = "Within 3 hours"
        elif h12_storm or h12_severe or tomorrow_storm:
            level  = ALERT_WATCH
            window = "Within 12 hours" if (h12_storm or h12_severe) else "Tomorrow"
        else:
            level  = ALERT_NONE
            window = "Clear"

        hazards = {
            "h1_storm":      h1_storm,
            "h1_wind":       h1_wind,
            "h1_rain":       h1_rain,
            "h3_storm":      h3_storm,
            "h3_wind":       h3_wind,
            "h3_severe":     h3_severe,
            "h12_storm":     h12_storm,
            "h12_severe":    h12_severe,
            "tomorrow_storm": tomorrow_storm,
        }

        return level, window, hazards

    def _build_detail(self, hazards: dict[str, bool]) -> str:
        """Build a human-readable detail string from hazard flags."""
        parts = []
        if hazards.get("h1_storm") or hazards.get("h3_storm") or hazards.get("h12_storm"):
            parts.append("Storm/Lightning")
        if hazards.get("h1_wind") or hazards.get("h3_wind"):
            parts.append("High Winds")
        if hazards.get("h1_rain"):
            parts.append("Heavy Rain")
        if hazards.get("h3_severe") or hazards.get("h12_severe"):
            parts.append("Severe Weather")
        if hazards.get("tomorrow_storm"):
            parts.append("Storm Tomorrow")
        return ", ".join(parts) if parts else "All Clear"