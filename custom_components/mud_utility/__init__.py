"""MUD Utilities integration."""

from __future__ import annotations

from aiohttp import ClientSession
from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
)

from .api import MudApi
from .const import (
    CONF_GAS_CONTRACT,
    CONF_WATER_CONTRACT,
)
from .coordinator import MudDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]


type MudUtilityConfigEntry = ConfigEntry[MudRuntimeData]


@dataclass
class MudRuntimeData:
    coordinator: MudDataUpdateCoordinator
    session: ClientSession


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MudUtilityConfigEntry,
) -> bool:
    """Set up MUD Utilities from a config entry."""
    session = async_create_clientsession(hass)
    api = MudApi(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_GAS_CONTRACT],
        entry.data[CONF_WATER_CONTRACT],
    )

    coordinator = MudDataUpdateCoordinator(
        hass,
        api,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        session.detach()
        raise

    entry.runtime_data = MudRuntimeData(
        coordinator=coordinator,
        session=session,
    )

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: MudUtilityConfigEntry,
) -> bool:
    """Unload MUD Utilities."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        entry.runtime_data.session.detach()

    return unload_ok
