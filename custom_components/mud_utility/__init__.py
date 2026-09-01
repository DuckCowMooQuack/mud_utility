"""MUD Utilities integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)

from .api import MudApi
from .const import (
    CONF_GAS_CONTRACT,
    CONF_WATER_CONTRACT,
)
from .coordinator import MudDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up MUD Utilities from a config entry."""
    api = MudApi(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_GAS_CONTRACT],
        entry.data[CONF_WATER_CONTRACT],
    )

    coordinator = MudDataUpdateCoordinator(
        hass,
        api,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload MUD Utilities."""
    return await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )
