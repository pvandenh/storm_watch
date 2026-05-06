"""Config flow for Storm Watch integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv

from .const import (
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
)

_LOGGER = logging.getLogger(__name__)


def _get_weather_entities(hass: HomeAssistant) -> list[str]:
    """Return all weather entity_ids currently registered."""
    registry = er.async_get(hass)
    return [
        entity.entity_id
        for entity in registry.entities.values()
        if entity.domain == WEATHER_DOMAIN
    ] or [e.entity_id for e in hass.states.async_all(WEATHER_DOMAIN)]


def _weather_selector(hass: HomeAssistant) -> vol.Schema:
    entities = _get_weather_entities(hass)
    return vol.In(entities) if entities else cv.string


class StormWatchConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate that the selected entities actually exist
            for key in (CONF_HOURLY_ENTITY, CONF_DAILY_ENTITY):
                entity_id = user_input.get(key, "")
                if not self.hass.states.get(entity_id):
                    errors[key] = "entity_not_found"

            if not errors:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOURLY_ENTITY]}_{user_input[CONF_DAILY_ENTITY]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Storm Watch",
                    data=user_input,
                )

        weather_entities = _get_weather_entities(self.hass)
        # Try to guess sensible defaults — hourly entity usually has "hourly" in name
        default_hourly = next(
            (e for e in weather_entities if "hourly" in e.lower()), ""
        )
        default_daily = next(
            (e for e in weather_entities if "hourly" not in e.lower()), ""
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOURLY_ENTITY, default=default_hourly): vol.In(weather_entities) if weather_entities else cv.string,
                vol.Required(CONF_DAILY_ENTITY,  default=default_daily):  vol.In(weather_entities) if weather_entities else cv.string,
                vol.Optional(CONF_SCAN_INTERVAL,    default=DEFAULT_SCAN_INTERVAL):    vol.All(int, vol.Range(min=5, max=120)),
                vol.Optional(CONF_WIND_EMERGENCY,   default=DEFAULT_WIND_EMERGENCY):   vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional(CONF_WIND_WARNING,     default=DEFAULT_WIND_WARNING):     vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional(CONF_PRECIP_EMERGENCY, default=DEFAULT_PRECIP_EMERGENCY): vol.All(vol.Coerce(float), vol.Range(min=0)),
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
                ): vol.All(int, vol.Range(min=5, max=120)),
                vol.Optional(
                    CONF_WIND_EMERGENCY,
                    default=current.get(CONF_WIND_EMERGENCY, DEFAULT_WIND_EMERGENCY),
                ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional(
                    CONF_WIND_WARNING,
                    default=current.get(CONF_WIND_WARNING, DEFAULT_WIND_WARNING),
                ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional(
                    CONF_PRECIP_EMERGENCY,
                    default=current.get(CONF_PRECIP_EMERGENCY, DEFAULT_PRECIP_EMERGENCY),
                ): vol.All(vol.Coerce(float), vol.Range(min=0)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
