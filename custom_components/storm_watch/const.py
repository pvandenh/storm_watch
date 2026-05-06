"""Constants for Storm Watch integration."""

DOMAIN = "storm_watch"
PLATFORMS = ["sensor", "binary_sensor"]

# Config flow keys
CONF_HOURLY_ENTITY = "hourly_weather_entity"
CONF_DAILY_ENTITY = "daily_weather_entity"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_WIND_EMERGENCY = "wind_speed_emergency"
CONF_WIND_WARNING = "wind_speed_warning"
CONF_PRECIP_EMERGENCY = "precipitation_emergency"
CONF_STORM_CONDITIONS = "storm_conditions"
CONF_SEVERE_CONDITIONS = "severe_conditions"

# Defaults
DEFAULT_SCAN_INTERVAL = 30  # minutes
DEFAULT_WIND_EMERGENCY = 60  # km/h
DEFAULT_WIND_WARNING = 50    # km/h
DEFAULT_PRECIP_EMERGENCY = 10  # mm per forecast slot (not mm/h)

# HA weather condition codes considered storm-class.
# These trigger Watch/Warning/Emergency depending on the time window.
# BOM mappings that reach these codes:
#   "storm" / "storms"          → "lightning-rainy"
#   "cyclone" / "tropical_cyclone" → "exceptional"
DEFAULT_STORM_CONDITIONS = [
    "lightning",
    "lightning-rainy",
    "thunderstorm",
    "hail",
    "tornado",
    "exceptional",
]

# HA weather condition codes considered severe (elevated risk, below storm).
# These trigger Watch/Warning depending on the time window.
#
# NOTE: "rainy" is intentionally included here because BOM maps both
# "heavy_shower" and "heavy_showers" to "rainy" — the same HA code used for
# light rain. Without this entry, heavy shower forecasts are invisible to
# Storm Watch's condition checker. The wind speed and precipitation threshold
# checks act as a secondary filter so ordinary rainy conditions don't
# unnecessarily escalate to Warning.
DEFAULT_SEVERE_CONDITIONS = [
    "pouring",
    "rainy",
    "windy-variant",
    "hurricane",
]

# Alert levels (ordered lowest → highest)
ALERT_NONE = "None"
ALERT_WATCH = "Watch"
ALERT_WARNING = "Warning"
ALERT_EMERGENCY = "Emergency"

ALERT_LEVELS = [ALERT_NONE, ALERT_WATCH, ALERT_WARNING, ALERT_EMERGENCY]

# Time windows in seconds
WINDOW_1H  = 3600
WINDOW_3H  = 10800
WINDOW_12H = 43200

# Coordinator data keys
KEY_LEVEL   = "level"
KEY_WINDOW  = "window"
KEY_DETAIL  = "detail"
KEY_HAZARDS = "hazards"
KEY_FORECASTS_HOURLY = "forecasts_hourly"
KEY_FORECASTS_DAILY  = "forecasts_daily"