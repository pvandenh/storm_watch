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
DEFAULT_PRECIP_EMERGENCY = 10  # mm/h

# HA weather condition codes considered storm-class
DEFAULT_STORM_CONDITIONS = [
    "lightning",
    "lightning-rainy",
    "thunderstorm",
    "hail",
    "tornado",
    "exceptional",
]

# HA weather condition codes considered severe (but below storm)
DEFAULT_SEVERE_CONDITIONS = [
    "pouring",
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
