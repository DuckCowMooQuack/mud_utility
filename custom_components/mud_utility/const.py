"""Constants for MUD Utilities integration."""

DOMAIN = "mud_utility"

BASE_URL = "https://myaccount.mudomaha.com"
LOGIN_URL = f"{BASE_URL}/sap/bc/ui5_ui5/sap/zmobius/index.html"

CONF_GAS_CONTRACT = "gas_contract"
CONF_WATER_CONTRACT = "water_contract"

CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"
DEFAULT_UPDATE_INTERVAL_HOURS = 24
MIN_UPDATE_INTERVAL_HOURS = 1
MAX_UPDATE_INTERVAL_HOURS = 720
