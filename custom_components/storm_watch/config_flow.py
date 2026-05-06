"""Config flow for Storm Watch integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er, selector

from .const import (
    CONF_DAILY_ENTITY,
    CONF_HOURLY_ENTITY,
    CONF_PRECIP_EMERGENCY,
    CONF_SCAN_INTERVAL,
    CONF_WIND_EMERGENCY,
    CONF_WIND_WARNING,
    DEFAULT_PRECIP_EMERGENCY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_WIND_EMERGENCY,
    DEFAULT_WIND_WARNING,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# HA weather supported_features bitmask values
_FEATURE_DAILY  = 1
_FEATURE_HOURLY = 2


def _get_weather_entities(hass: HomeAssistant) -> list[str]:
    """Return all weather entity_ids currently registered."""
    registry = er.async_get(hass)
    return (
        [
            entity.entity_id
            for entity in registry.entities.values()
            if entity.domain == WEATHER_DOMAIN
        ]
        or [e.entity_id for e in hass.states.async_all(WEATHER_DOMAIN)]
    )


def _supports_forecast(hass: HomeAssistant, entity_id: str, feature_bit: int) -> bool:
    """Return True if the weather entity advertises support for a forecast type.

    HA weather supported_features bitmask:
      WeatherEntityFeature.FORECAST_DAILY   = 1
      WeatherEntityFeature.FORECAST_HOURLY  = 2
    """
    state = hass.states.get(entity_id)
    if state is None:
        return False
    try:
        features = int(state.attributes.get("supported_features", 0))
    except (TypeError, ValueError):
        return False
    return bool(features & feature_bit)


class StormWatchConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            hourly_id = user_input.get(CONF_HOURLY_ENTITY, "")
            daily_id  = user_input.get(CONF_DAILY_ENTITY, "")

            # Existence check
            if not self.hass.states.get(hourly_id):
                errors[CONF_HOURLY_ENTITY] = "entity_not_found"
            if not self.hass.states.get(daily_id):
                errors[CONF_DAILY_ENTITY] = "entity_not_found"

            # Feature-support checks (only when entities exist)
            if not errors:
                if not _supports_forecast(self.hass, hourly_id, _FEATURE_HOURLY):
                    errors[CONF_HOURLY_ENTITY] = "no_hourly_support"
                if not _supports_forecast(self.hass, daily_id, _FEATURE_DAILY):
                    errors[CONF_DAILY_ENTITY] = "no_daily_support"

            if not errors:
                await self.async_set_unique_id(f"{hourly_id}_{daily_id}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Storm Watch", data=user_input)

        weather_entities = _get_weather_entities(self.hass)

        # Pick smarter defaults using feature flags rather than name heuristics
        default_hourly = next(
            (e for e in weather_entities if _supports_forecast(self.hass, e, _FEATURE_HOURLY)
             and not _supports_forecast(self.hass, e, _FEATURE_DAILY)),
            next((e for e in weather_entities if _supports_forecast(self.hass, e, _FEATURE_HOURLY)), ""),
        )
        default_daily = next(
            (e for e in weather_entities if _supports_forecast(self.hass, e, _FEATURE_DAILY)
             and not _supports_forecast(self.hass, e, _FEATURE_HOURLY)),
            next((e for e in weather_entities if _supports_forecast(self.hass, e, _FEATURE_DAILY)), ""),
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOURLY_ENTITY, default=default_hourly): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="weather", multiple=False)
                ),
                vol.Required(CONF_DAILY_ENTITY, default=default_daily): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="weather", multiple=False)
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=120, step=1, mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Optional(CONF_WIND_EMERGENCY, default=DEFAULT_WIND_EMERGENCY): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=200, step=1, unit_of_measurement="km/h", mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_WIND_WARNING, default=DEFAULT_WIND_WARNING): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=200, step=1, unit_of_measurement="km/h", mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_PRECIP_EMERGENCY, default=DEFAULT_PRECIP_EMERGENCY): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=0.5, unit_of_measurement="mm", mode=selector.NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "hourly_help": "Select your hourly weather forecast entity (supported_features=2)",
                "daily_help":  "Select your daily weather forecast entity (supported_features=1)",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> StormWatchOptionsFlow:
        return StormWatchOptionsFlow(config_entry)


class StormWatchOptionsFlow(OptionsFlow):
    """Handle options updates (thresholds, scan interval) without re-setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options or self.config_entry.data

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=120, step=1, mode=selector.NumberSelectorMode.SLIDER)
                ),
                vol.Optional(
                    CONF_WIND_EMERGENCY,
                    default=current.get(CONF_WIND_EMERGENCY, DEFAULT_WIND_EMERGENCY),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=200, step=1, unit_of_measurement="km/h", mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(
                    CONF_WIND_WARNING,
                    default=current.get(CONF_WIND_WARNING, DEFAULT_WIND_WARNING),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=200, step=1, unit_of_measurement="km/h", mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(
                    CONF_PRECIP_EMERGENCY,
                    default=current.get(CONF_PRECIP_EMERGENCY, DEFAULT_PRECIP_EMERGENCY),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=0.5, unit_of_measurement="mm", mode=selector.NumberSelectorMode.BOX)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)