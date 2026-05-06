# 🌩️ Storm Watch

**Advanced storm alerting for Home Assistant.**

Storm Watch wraps any Home Assistant weather integration that supports forecast service calls (BOM, Met.no, OpenWeatherMap, etc.) and turns raw forecast data into a tiered alert system — giving you actionable sensors you can use to automate storm preparation before severe weather arrives.

---

## Features

- **Tiered alert levels** — `None` → `Watch` → `Warning` → `Emergency`, computed from hourly and daily forecast data
- **12 granular sensors** — 3 state sensors and 9 binary sensors covering individual hazard types across 1h, 3h and 12h windows
- **Configurable thresholds** — set your own wind speed and precipitation limits via the UI, no YAML required
- **Works with any forecast provider** — BOM, Met.no, OpenWeatherMap, or any integration that exposes `weather.get_forecasts`
- **Fully UI-configurable** — set up and adjust through Settings → Devices & Services, no `configuration.yaml` edits needed

---

## How it works

Storm Watch polls your hourly and daily weather forecast entities on a configurable schedule. Each update it scans forecast slots across three time windows and checks for storm-class conditions, dangerous wind speeds, and heavy rainfall. The results are exposed as HA sensors your automations can act on immediately.

```
Hourly forecast ──┐
                  ├──► Coordinator ──► Alert Level sensor  (None/Watch/Warning/Emergency)
Daily forecast  ──┘         │
                            ├──► Window sensor       (e.g. "Within 3 hours")
                            ├──► Detail sensor        (e.g. "Storm/Lightning, High Winds")
                            └──► 9 × Binary sensors   (per-hazard flags)
```

### Alert levels

| Level | Meaning |
|---|---|
| `None` | No storm risk detected in any window |
| `Watch` | Storm or severe conditions possible within 12 hours or tomorrow |
| `Warning` | Storm, high winds, or severe conditions within 3 hours |
| `Emergency` | Storm conditions or wind + heavy rain within the next hour |

---

## Installation

### Via HACS (recommended)

1. In Home Assistant, open **HACS → ⋮ → Custom repositories**
2. Add the URL of this repository and set the category to **Integration**
3. Find **Storm Watch** in HACS and click **Download**
4. Restart Home Assistant

### Manual

Copy the `custom_components/storm_watch/` folder into your HA config directory under `custom_components/`, then restart Home Assistant.

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Storm Watch**
3. Select your hourly and daily weather forecast entities
4. Configure your alert thresholds (or leave the defaults)

> **BOM users:** your entities will typically be named `weather.xxx_hourly` and `weather.forecast_home` (or similar). Both will appear in the entity picker automatically.

---

## Sensors

### State sensors

| Entity | Description | Example state |
|---|---|---|
| `sensor.storm_watch_alert_level` | Primary tiered alert level | `Warning` |
| `sensor.storm_watch_alert_window` | Earliest window with detected risk | `Within 3 hours` |
| `sensor.storm_watch_alert_detail` | Human-readable hazard summary | `Storm/Lightning, High Winds` |

The **Alert Level** sensor also exposes all hazard flags and configured thresholds as attributes, making it easy to build detailed Lovelace cards.

### Binary sensors

| Entity | On when… |
|---|---|
| `binary_sensor.storm_watch_h1_storm` | Storm condition forecast within 1 hour |
| `binary_sensor.storm_watch_h1_wind` | Emergency wind speed within 1 hour |
| `binary_sensor.storm_watch_h1_rain` | Emergency precipitation within 1 hour |
| `binary_sensor.storm_watch_h3_storm` | Storm condition within 3 hours |
| `binary_sensor.storm_watch_h3_wind` | Warning-level wind within 3 hours |
| `binary_sensor.storm_watch_h3_severe` | Severe weather within 3 hours |
| `binary_sensor.storm_watch_h12_storm` | Storm condition within 12 hours |
| `binary_sensor.storm_watch_h12_severe` | Severe weather within 12 hours |
| `binary_sensor.storm_watch_tomorrow` | Storm forecast in tomorrow's daily data |
| `binary_sensor.storm_watch_any_1h` | Any emergency-class risk within 1 hour |
| `binary_sensor.storm_watch_any_3h` | Any warning-class risk within 3 hours |
| `binary_sensor.storm_watch_any_12h` | Any watch-class risk within 12 hours |

---

## Configuration options

These can be changed at any time via **Settings → Devices & Services → Storm Watch → Configure** without reinstalling.

| Option | Default | Description |
|---|---|---|
| Update interval | 30 min | How often forecasts are fetched |
| Emergency wind speed | 60 km/h | Wind threshold for Emergency alerts |
| Warning wind speed | 50 km/h | Wind threshold for Warning alerts |
| Emergency precipitation | 10 mm | Rain threshold contributing to Emergency alerts |

---

## Automation examples

**Close the skylights when a storm is imminent:**
```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.storm_watch_any_1h
    to: "on"
action:
  - service: cover.close_cover
    target:
      entity_id: cover.skylights
```

**Send a notification when a Watch is issued:**
```yaml
trigger:
  - platform: state
    entity_id: sensor.storm_watch_alert_level
    to: "Watch"
action:
  - service: notify.mobile_app
    data:
      title: "Storm Watch ⚠️"
      message: "Storm conditions possible {{ states('sensor.storm_watch_alert_window') | lower }}. {{ states('sensor.storm_watch_alert_detail') }}."
```

**Push an emergency alert for imminent storms:**
```yaml
trigger:
  - platform: state
    entity_id: sensor.storm_watch_alert_level
    to: "Emergency"
action:
  - service: notify.mobile_app
    data:
      title: "🚨 Storm Emergency"
      message: "{{ states('sensor.storm_watch_alert_detail') }} detected within the next hour. Take action now."
```

---

## Storm and severe conditions

Storm Watch classifies HA weather condition codes into two tiers:

**Storm-class** (highest severity — triggers Watch/Warning/Emergency):
`lightning`, `lightning-rainy`, `thunderstorm`, `hail`, `tornado`, `exceptional`

**Severe-class** (elevated severity — triggers Watch/Warning):
`pouring`, `windy-variant`, `hurricane`

These lists are built-in for now. Custom condition lists are planned for a future release.

---

## Requirements

- Home Assistant 2024.1.0 or newer
- At least one weather integration that supports `weather.get_forecasts` with hourly forecasts
- A separate daily forecast entity is recommended for tomorrow storm detection but not strictly required

---

## Contributing

Bug reports and pull requests are welcome. Please open an issue first for any significant changes.

---

## License

MIT
