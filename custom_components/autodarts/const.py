"""Constants for the Autodarts integration."""

from typing import Final

DOMAIN: Final = "autodarts"

DEFAULT_PORT: Final = 3180
DEFAULT_SCAN_INTERVAL: Final = 5  # seconds

# Config entry keys
CONF_TOKEN: Final = "token"
CONF_CLIENT_ID: Final = "client_id"
CONF_LOCAL_ONLY: Final = "local_only"
CONF_BOARD_ID: Final = "board_id"
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
# Major Board Manager version the entities were built for (1 classic, 2 headless).
CONF_API_GENERATION: Final = "api_generation"

# Autodarts' guide to the headless Board Manager 2, which replaces the app.
BOARD_MANAGER_2_URL: Final = (
    "https://docs.autodarts.com/getting-started/detection/headless-installation/"
)

# Lists boards on the same public network, as the Board Manager app does.
DISCOVERY_URL: Final = "https://discover.autodarts.com"

PLATFORMS: Final = [
    "sensor",
    "binary_sensor",
    "button",
    "switch",
    "select",
    "camera",
    "event",
    "update",
]

# Sensor keys — board
SENSOR_BOARD_STATUS: Final = "board_status"
SENSOR_BOARD_EVENT: Final = "board_event"

# Sensor keys — match
SENSOR_GAME_MODE: Final = "game_mode"
SENSOR_MATCH_STATE: Final = "match_state"
SENSOR_ROUND: Final = "round"

# Sensor keys — detection
SENSOR_LAST_THROW: Final = "last_throw"
SENSOR_NUM_THROWS: Final = "num_throws"
SENSOR_VISIT_SCORE: Final = "visit_score"
SENSOR_DARTS_THROWN: Final = "darts_thrown"
