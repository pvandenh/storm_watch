"""Storm Watch — advanced storm alerting for Home Assistant.

Wraps any weather integration that supports forecast service calls
(BOM, Met.no, OpenWeatherMap, etc.) and exposes a tiered alert sensor
plus granular binary sensors for each hazard type and time window.
"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import StormWatchCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Storm Watch from a config entry."""
    coordinator = StormWatchCoordinator(hass, entry)

    # Do an initial fetch so entities have data on first load
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward setup to sensor and binary_sensor platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Re-run coordinator when options are updated (threshold changes)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options change so new thresholds take effect."""
    await hass.config_entries.async_reload(entry.entry_id)
