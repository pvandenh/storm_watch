"""Binary sensor platform for Storm Watch.

Exposes each hazard flag from the coordinator as an individual binary sensor,
plus one per-window "any storm risk" sensor. This gives automations granular
hooks without needing to parse the detail string from the main sensor.

Sensors created:
  Per-hazard (on = hazard detected):
    binary_sensor.storm_watch_h1_storm      — storm condition within 1 h
    binary_sensor.storm_watch_h1_wind       — emergency wind within 1 h
    binary_sensor.storm_watch_h1_rain       — emergency rain within 1 h
    binary_sensor.storm_watch_h3_storm      — storm condition within 3 h
    binary_sensor.storm_watch_h3_wind       — warning-level wind within 3 h
    binary_sensor.storm_watch_h3_severe     — severe condition within 3 h
    binary_sensor.storm_watch_h12_storm     — storm condition within 12 h
    binary_sensor.storm_watch_h12_severe    — severe condition within 12 h
    binary_sensor.storm_watch_tomorrow      — storm forecast tomorrow (daily)

  Convenience roll-ups (on = any risk in that window):
    binary_sensor.storm_watch_any_1h        — any emergency-class risk ≤ 1 h
    binary_sensor.storm_watch_any_3h        — any warning-class risk ≤ 3 h
    binary_sensor.storm_watch_any_12h       — any watch-class risk ≤ 12 h
"""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, KEY_HAZARDS
from .coordinator import StormWatchCoordinator


@dataclass(frozen=True)
class StormWatchBinarySensorDescription(BinarySensorEntityDescription):
    """Extends the standard description with Storm Watch–specific fields."""

    # Key(s) inside coordinator.data[KEY_HAZARDS] that drive this sensor.
    # If multiple keys are listed the sensor is ON when *any* of them is True.
    hazard_keys: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Sensor catalogue
# ---------------------------------------------------------------------------

BINARY_SENSOR_DESCRIPTIONS: tuple[StormWatchBinarySensorDescription, ...] = (
    # ── Per-hazard sensors ──────────────────────────────────────────────────
    StormWatchBinarySensorDescription(
        key="h1_storm",
        name="Storm Within 1 Hour",
        icon="mdi:weather-lightning",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h1_storm",),
    ),
    StormWatchBinarySensorDescription(
        key="h1_wind",
        name="Emergency Wind Within 1 Hour",
        icon="mdi:weather-windy",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h1_wind",),
    ),
    StormWatchBinarySensorDescription(
        key="h1_rain",
        name="Heavy Rain Within 1 Hour",
        icon="mdi:weather-pouring",
        device_class=BinarySensorDeviceClass.MOISTURE,
        hazard_keys=("h1_rain",),
    ),
    StormWatchBinarySensorDescription(
        key="h3_storm",
        name="Storm Within 3 Hours",
        icon="mdi:weather-lightning-rainy",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h3_storm",),
    ),
    StormWatchBinarySensorDescription(
        key="h3_wind",
        name="High Winds Within 3 Hours",
        icon="mdi:weather-windy",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h3_wind",),
    ),
    StormWatchBinarySensorDescription(
        key="h3_severe",
        name="Severe Weather Within 3 Hours",
        icon="mdi:weather-lightning-rainy",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h3_severe",),
    ),
    StormWatchBinarySensorDescription(
        key="h12_storm",
        name="Storm Within 12 Hours",
        icon="mdi:weather-lightning-rainy",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h12_storm",),
    ),
    StormWatchBinarySensorDescription(
        key="h12_severe",
        name="Severe Weather Within 12 Hours",
        icon="mdi:weather-rainy",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h12_severe",),
    ),
    StormWatchBinarySensorDescription(
        key="tomorrow_storm",
        name="Storm Forecast Tomorrow",
        icon="mdi:calendar-alert",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("tomorrow_storm",),
    ),
    # ── Convenience roll-ups ────────────────────────────────────────────────
    StormWatchBinarySensorDescription(
        key="any_1h",
        name="Any Storm Risk Within 1 Hour",
        icon="mdi:alert",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h1_storm", "h1_wind", "h1_rain"),
    ),
    StormWatchBinarySensorDescription(
        key="any_3h",
        name="Any Storm Risk Within 3 Hours",
        icon="mdi:alert-outline",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h3_storm", "h3_wind", "h3_severe"),
    ),
    StormWatchBinarySensorDescription(
        key="any_12h",
        name="Any Storm Risk Within 12 Hours",
        icon="mdi:weather-cloudy-alert",
        device_class=BinarySensorDeviceClass.SAFETY,
        hazard_keys=("h12_storm", "h12_severe", "tomorrow_storm"),
    ),
)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Storm Watch binary sensors from a config entry."""
    coordinator: StormWatchCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        StormWatchBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return shared device info so all entities group under one device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Storm Watch",
        manufacturer="Storm Watch",
        model="Storm Alert System",
        sw_version="0.0.1",
    )


class StormWatchBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """A binary sensor driven by a hazard flag (or OR of flags) from the coordinator."""

    entity_description: StormWatchBinarySensorDescription

    def __init__(
        self,
        coordinator: StormWatchCoordinator,
        entry: ConfigEntry,
        description: StormWatchBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = _device_info(entry)

    @property
    def is_on(self) -> bool | None:
        """Return True if any of the tracked hazard keys are active."""
        if self.coordinator.data is None:
            return None
        hazards: dict[str, bool] = self.coordinator.data.get(KEY_HAZARDS, {})
        return any(hazards.get(k, False) for k in self.entity_description.hazard_keys)

    @property
    def extra_state_attributes(self) -> dict:
        """Expose the individual hazard flags that feed this sensor."""
        if self.coordinator.data is None:
            return {}
        hazards: dict[str, bool] = self.coordinator.data.get(KEY_HAZARDS, {})
        return {
            k: hazards.get(k, False)
            for k in self.entity_description.hazard_keys
        }