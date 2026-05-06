# 🌩️ Storm Watch

A custom Home Assistant integration that wraps any standard weather integration (BOM, Met.no, OpenWeatherMap, etc.) and provides tiered storm alerts across multiple time windows — giving you granular sensors and binary sensors to drive automations before severe weather hits.

---

## Features

- **Four alert levels**: None → Watch → Warning → Emergency
- **Three time windows**: 1 hour, 3 hours, and 12 hours, plus a tomorrow outlook
- **Per-hazard binary sensors** for fine-grained automation triggers
- **Convenience roll-up sensors** for each time window
- **Configurable thresholds** for wind speed and precipitation
- **Works with any HA weather integration** that supports `weather.get_forecasts`
- **Options flow** — update thresholds at any time without re-setup

---

## Alert Levels

| Level | Meaning |
|-----------|-------------------------------------------------------------------------|
| `None` | No storm conditions detected |
| `Watch` | Storm-class or severe conditions possible within 12 hours or tomorrow |
| `Warning` | Storm-class or high winds detected within 3 hours |
| `Emergency` | Storm conditions or combined wind + heavy rain within 1 hour |

---

## Sensors

### Main Sensors

| Entity | Description |
|--------------------------------------|----------------------------------------------|
| `sensor.storm_watch_alert_level` | Current alert level (None/Watch/Warning/Emergency) |
| `sensor.storm_watch_alert_window` | Earliest time window with detected risk |
| `sensor.storm_watch_alert_detail` | Human-readable summary of active hazards |

The alert level sensor also exposes all hazard flags, configured thresholds, and the detail/window as attributes.

### Binary Sensors — Per Hazard

| Entity | On when... |
|--------------------------------------------------|--------------------------------------|
| `binary_sensor.storm_watch_storm_within_1_hour` | Storm condition code in next 1 hour |
| `binary_sensor.storm_watch_emergency_wind_within_1_hour` | Wind > emergency threshold in next 1 hour |
| `binary_sensor.storm_watch_heavy_rain_within_1_hour` | Precipitation > emergency threshold in next 1 hour |
| `binary_sensor.storm_watch_storm_within_3_hours` | Storm condition code in next 3 hours |
| `binary_sensor.storm_watch_high_winds_within_3_hours` | Wind > warning threshold in next 3 hours |
| `binary_sensor.storm_watch_severe_weather_within_3_hours` | Severe condition code in next 3 hours |
| `binary_sensor.storm_watch_storm_within_12_hours` | Storm condition code in next 12 hours |
| `binary_sensor.storm_watch_severe_weather_within_12_hours` | Severe condition + threshold breach in next 12 hours |
| `binary_sensor.storm_watch_storm_forecast_tomorrow` | Storm-class condition code forecast for tomorrow |

### Binary Sensors — Convenience Roll-ups

| Entity | On when... |
|----------------------------------------------------|--------------------------------------------|
| `binary_sensor.storm_watch_any_storm_risk_within_1_hour` | Any 1-hour hazard is active |
| `binary_sensor.storm_watch_any_storm_risk_within_3_hours` | Any 3-hour hazard is active |
| `binary_sensor.storm_watch_any_storm_risk_within_12_hours` | Any 12-hour or tomorrow hazard is active |

---

## Configuration

During setup you select two weather entities and configure alert thresholds. All thresholds can be updated later via **Settings → Integrations → Storm Watch → Configure**.

| Setting | Default | Description |
|-------------------------------|---------|--------------------------------------------------|
| Hourly forecast entity | — | Weather entity with hourly forecast support |
| Daily forecast entity | — | Weather entity with daily forecast support |
| Update interval | 30 min | How often forecasts are fetched |
| Emergency wind speed | 60 km/h | Triggers wind hazard flags in the 1-hour window |
| Warning wind speed | 50 km/h | Triggers wind hazard flags in the 3-hour window |
| Emergency precipitation | 10 mm | Triggers rain hazard flag in the 1-hour window |

> **Note:** A single weather entity that supports both daily and hourly forecasts (e.g. Met.no, `supported_features: 3`) can be used for both fields.

<img width="124" height="317" alt="image" src="https://github.com/user-attachments/assets/c70cd961-1a9b-4e1c-a835-887081f3ef2f" />

---

## Supported Weather Integrations

Any integration that implements the standard `weather.get_forecasts` service call works with Storm Watch. Tested with:

| Integration | Notes |
|---|---|
| **BOM** (Bureau of Meteorology) | Use the hourly entity for hourly and the daily entity for daily |
| **Met.no** (Meteorologisk institutt) | Single entity supports both hourly and daily |
| **OpenWeatherMap** | Hourly and daily entities configured separately |

### Weather Condition Codes

Storm Watch uses two tiers of HA standard condition codes internally:

**Storm-class** (trigger Watch/Warning/Emergency depending on window):
`lightning`, `lightning-rainy`, `thunderstorm`, `hail`, `tornado`, `exceptional`

**Severe-class** (trigger Watch/Warning in shorter windows, require threshold confirmation at 12 h):
`pouring`, `rainy`, `windy-variant`, `hurricane`

---

## Installation

1. Open HACS in the Home Assistant sidebar.
2. Click the ⋮ menu → Custom repositories.
3. Add repository: https://github.com/pvandenh/storm_watch, category: Integration.
2. Restart Home Assistant.
3. Go to **Settings → Devices and Services → Add Integration** and search for **Storm Watch**.
4. Select your hourly and daily forecast entities and set your thresholds.

---

## Requirements

- Home Assistant with at least one weather integration that supports `weather.get_forecasts`
- No additional Python packages required

---

## Links

- [Documentation](https://github.com/pvandenh/storm_watch)
- [Issue Tracker](https://github.com/pvandenh/storm_watch/issues)
