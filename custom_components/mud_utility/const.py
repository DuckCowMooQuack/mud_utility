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

# M.U.D. reports gas in therms ("TH"), which the Energy Dashboard cannot use.
# Gas measured as energy is accepted, so gas statistics are converted to kWh.
# 1 therm (U.S.) = 1.054804e8 J (NIST SP 811) and 1 kWh = 3.6e6 J. This is the
# same definition Home Assistant uses for its own "thm" unit.
THERM_TO_KWH = 1.054804e8 / 3.6e6
