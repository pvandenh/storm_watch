"""Sensor platform for Storm Watch.

Creates three sensors:
  sensor.storm_watch_alert_level  — None / Watch / Warning / Emergency
  sensor.storm_watch_window       — e.g. "Within 3 hours"
  sensor.storm_watch_detail       — e.g. "Storm/Lightning, High Winds"
"""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ALERT_EMERGENCY,
    ALERT_LEVELS,
    ALERT_NONE,
    ALERT_WARNING,
    ALERT_WATCH,
    DOMAIN,
    KEY_DETAIL,
    KEY_HAZARDS,
    KEY_LEVEL,
    KEY_WINDOW,
)
from .coordinator import StormWatchCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StormWatchCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        StormAlertLevelSensor(coordinator, entry),
        StormAlertWindowSensor(coordinator, entry),
        StormAlertDetailSensor(coordinator, entry),
    ])


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Storm Watch",
        manufacturer="Storm Watch",
        model="Storm Alert System",
        sw_version="1.0.0",
    )


class StormWatchSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for all Storm Watch sensors."""

    def __init__(
        self,
        coordinator: StormWatchCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        unique_suffix: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_icon = icon
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)


class StormAlertLevelSensor(StormWatchSensorBase):
    """Primary alert level sensor — state is None/Watch/Warning/Emergency."""

    def __init__(self, coordinator: StormWatchCoordinator, entry: ConfigEntry) -> None:
        super().__init__(
            coordinator, entry,
            key=KEY_LEVEL,
            name="Storm Alert Level",
            unique_suffix="alert_level",
            icon="mdi:weather-lightning-rainy",
        )
        self._attr_options = ALERT_LEVELS
        self._attr_device_class = SensorDeviceClass.ENUM

    @property
    def extra_state_attributes(self) -> dict:
        """Expose all hazard flags and config thresholds as attributes."""
        data = self.coordinator.data or {}
        hazards = data.get(KEY_HAZARDS, {})
        entry_data = {**self._entry.data, **self._entry.options}
        return {
            "window":             data.get(KEY_WINDOW, "Unknown"),
            "detail":             data.get(KEY_DETAIL, "Unknown"),
            # Individual hazard flags
            **{f"hazard_{k}": v for k, v in hazards.items()},
            # Configured thresholds (useful for card display)
            "threshold_wind_emergency":   entry_data.get("wind_speed_emergency", 60),
            "threshold_wind_warning":     entry_data.get("wind_speed_warning", 50),
            "threshold_precip_emergency": entry_data.get("precipitation_emergency", 10),
        }

    @property
    def icon(self) -> str:
        level = self.native_value
        return {
            ALERT_EMERGENCY: "mdi:weather-lightning",
            ALERT_WARNING:   "mdi:weather-lightning-rainy",
            ALERT_WATCH:     "mdi:weather-rainy",
            ALERT_NONE:      "mdi:weather-sunny",
        }.get(level, "mdi:weather-cloudy")


class StormAlertWindowSensor(StormWatchSensorBase):
    """Sensor reporting the earliest time window with storm risk."""

    def __init__(self, coordinator: StormWatchCoordinator, entry: ConfigEntry) -> None:
        super().__init__(
            coordinator, entry,
            key=KEY_WINDOW,
            name="Storm Alert Window",
            unique_suffix="alert_window",
            icon="mdi:calendar-clock",
        )


class StormAlertDetailSensor(StormWatchSensorBase):
    """Sensor reporting what hazards were detected."""

    def __init__(self, coordinator: StormWatchCoordinator, entry: ConfigEntry) -> None:
        super().__init__(
            coordinator, entry,
            key=KEY_DETAIL,
            name="Storm Alert Detail",
            unique_suffix="alert_detail",
            icon="mdi:weather-rainy",
        )