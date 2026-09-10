"""MUD Utilities integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from aiohttp import ClientSession
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
    CONF_UPDATE_INTERVAL_HOURS,
    CONF_WATER_CONTRACT,
    DEFAULT_UPDATE_INTERVAL_HOURS,
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

    interval_hours = entry.options.get(
        CONF_UPDATE_INTERVAL_HOURS,
        DEFAULT_UPDATE_INTERVAL_HOURS,
    )

    coordinator = MudDataUpdateCoordinator(
        hass,
        api,
        update_interval=timedelta(hours=interval_hours),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await session.close()
        raise

    entry.runtime_data = MudRuntimeData(
        coordinator=coordinator,
        session=session,
    )

    entry.async_on_unload(
        entry.add_update_listener(
            _async_update_listener
        )
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
        await entry.runtime_data.session.close()

    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant,
    entry: MudUtilityConfigEntry,
) -> None:
    """Reload MUD Utilities when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
