"""Data coordinator for MUD Utilities Test."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
)
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util.unit_conversion import (
    VolumeConverter,
)

from .api import (
    MudApi,
    MudApiError,
    MudAuthError,
)
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

GAS_STATISTIC_ID = (
    f"{DOMAIN}:gas_consumption"
)

WATER_STATISTIC_ID = (
    f"{DOMAIN}:water_consumption"
)


class MudDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, Any]]
):
    """Fetch MUD Utilities Test data and maintain historical statistics."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MudApi,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

        self.api = api

    async def _async_update_data(
        self,
    ) -> dict[str, Any]:
        """Refresh MUD Utilities Test and import historical statistics."""
        try:
            data = await self.api.async_fetch_all()

        except MudAuthError as err:
            raise ConfigEntryAuthFailed(
                str(err)
            ) from err

        except (
            MudApiError,
            ClientError,
            asyncio.TimeoutError,
        ) as err:
            raise UpdateFailed(
                str(err)
            ) from err

        self._import_history(
            data,
        )

        return data

    def _import_history(
        self,
        data: dict[str, Any],
    ) -> None:
        """Import all known gas and water billing-cycle history."""
        self._import_utility_history(
            utility="gas",
            history=data["gas"]["history"],
            statistic_id=GAS_STATISTIC_ID,
            name="MUD Utilities Test Gas Consumption",
            unit="TH",
            unit_class=None,
        )

        self._import_utility_history(
            utility="water",
            history=data["water"]["history"],
            statistic_id=WATER_STATISTIC_ID,
            name="MUD Utilities Test Water Consumption",
            unit=UnitOfVolume.CENTUM_CUBIC_FEET,
            unit_class=VolumeConverter.UNIT_CLASS,
        )

    def _import_utility_history(
        self,
        *,
        utility: str,
        history: list[dict[str, Any]],
        statistic_id: str,
        name: str,
        unit: str,
        unit_class: str | None,
    ) -> None:
        """Import one utility's billing-cycle records."""
        metadata = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=name,
            source=DOMAIN,
            statistic_id=statistic_id,
            unit_class=unit_class,
            unit_of_measurement=unit,
        )

        statistics: list[
            StatisticData
        ] = []

        cumulative_sum = 0.0

        for record in history:
            value = record.get(
                "consumption"
            )

            timestamp = (
                record.get("period_end")
                or record.get("period_start")
            )

            if not isinstance(
                value,
                (int, float),
            ):
                continue

            if timestamp is None:
                continue

            value = float(value)

            cumulative_sum += value

            statistics.append(
                StatisticData(
                    start=timestamp,
                    state=value,
                    sum=cumulative_sum,
                )
            )

        if not statistics:
            _LOGGER.warning(
                "No valid %s history available "
                "for statistics import",
                utility,
            )
            return

        _LOGGER.info(
            "Importing %d M.U.D. %s "
            "billing-cycle history records",
            len(statistics),
            utility,
        )

        async_add_external_statistics(
            self.hass,
            metadata,
            statistics,
        )
