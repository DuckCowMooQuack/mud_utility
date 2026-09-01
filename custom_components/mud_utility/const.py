"""Constants for MUD Utilities integration."""

from datetime import timedelta

DOMAIN = "mud_utility"

BASE_URL = "https://myaccount.mudomaha.com"
LOGIN_URL = f"{BASE_URL}/sap/bc/ui5_ui5/sap/zmobius/index.html"

CONF_GAS_CONTRACT = "gas_contract"
CONF_WATER_CONTRACT = "water_contract"

UPDATE_INTERVAL = timedelta(hours=24)
