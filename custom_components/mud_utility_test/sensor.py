"""Sensors for MUD Utilities Test."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import (
    ConfigEntry,
)
from homeassistant.core import (
    HomeAssistant,
)
from homeassistant.helpers.device_registry import (
    DeviceInfo,
)
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN
from .coordinator import (
    MudDataUpdateCoordinator,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MUD Utilities Test sensors."""
    coordinator: MudDataUpdateCoordinator = (
        entry.runtime_data
    )

    async_add_entities(
        [
            MudConsumptionSensor(
                coordinator,
                entry,
                "gas",
            ),
            MudConsumptionSensor(
                coordinator,
                entry,
                "water",
            ),
            MudLastRefreshSensor(
                coordinator,
                entry,
            ),
        ]
    )


class MudBaseSensor(
    CoordinatorEntity[
        MudDataUpdateCoordinator
    ],
    SensorEntity,
):
    """Base sensor for MUD Utilities Test."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MudDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(
            coordinator
        )

        self._attr_device_info = (
            DeviceInfo(
                identifiers={
                    (
                        DOMAIN,
                        entry.entry_id,
                    )
                },
                name="MUD Utilities Test",
                manufacturer=(
                    "Metropolitan "
                    "Utilities District"
                ),
                model="Customer Portal",
            )
        )


class MudConsumptionSensor(
    MudBaseSensor
):
    """Latest M.U.D. billing-cycle consumption."""

    def __init__(
        self,
        coordinator: MudDataUpdateCoordinator,
        entry: ConfigEntry,
        utility: str,
    ) -> None:
        super().__init__(
            coordinator,
            entry,
        )

        self._utility = utility

        self._attr_unique_id = (
            f"{entry.entry_id}_"
            f"{utility}_consumption"
        )

        self._attr_name = (
            f"{utility.title()} Consumption"
        )

        self._attr_icon = (
            "mdi:fire"
            if utility == "gas"
            else "mdi:water"
        )

    @property
    def _utility_data(
        self,
    ) -> dict[str, Any]:
        return self.coordinator.data[
            self._utility
        ]

    @property
    def _latest(
        self,
    ) -> dict[str, Any]:
        return self._utility_data[
            "latest"
        ]

    @property
    def native_value(
        self,
    ) -> float | str | None:
        return self._latest.get(
            "consumption"
        )

    @property
    def native_unit_of_measurement(
        self,
    ) -> str | None:
        return self._latest.get(
            "unit"
        )

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        latest = self._latest

        history = self._utility_data[
            "history"
        ]

        first = (
            history[0]
            if history
            else {}
        )

        return {
            "billing_period":
                latest.get(
                    "billing_period"
                ),
            "period_start":
                self._date_string(
                    latest.get(
                        "period_start"
                    )
                ),
            "period_end":
                self._date_string(
                    latest.get(
                        "period_end"
                    )
                ),
            "reading_category":
                latest.get(
                    "reading_category"
                ),
            "reading_category_id":
                latest.get(
                    "reading_category_id"
                ),
            "contract_id":
                self._utility_data.get(
                    "contract_id"
                ),
            "history_records":
                len(history),
            "history_start":
                self._date_string(
                    first.get(
                        "period_start"
                    )
                ),
            "history_end":
                self._date_string(
                    latest.get(
                        "period_end"
                    )
                ),
            # Preserve every billing-cycle record so dashboard
            # cards can display the exact M.U.D. meter periods
            # instead of re-bucketing them into calendar months.
            "billing_history": [
                {
                    "start":
                        self._date_string(
                            record.get(
                                "period_start"
                            )
                        ),
                    "end":
                        self._date_string(
                            record.get(
                                "period_end"
                            )
                        ),
                    "billing_period":
                        record.get(
                            "billing_period"
                        ),
                    "consumption":
                        record.get(
                            "consumption"
                        ),
                    "unit":
                        record.get(
                            "unit"
                        ),
                    "reading_category":
                        record.get(
                            "reading_category"
                        ),
                }
                for record in history
            ],
        }

    @staticmethod
    def _date_string(
        value,
    ) -> str | None:
        """Convert a datetime value to YYYY-MM-DD."""
        if value is None:
            return None

        return value.date().isoformat()


class MudLastRefreshSensor(
    MudBaseSensor
):
    """Last successful M.U.D. refresh."""

    _attr_device_class = (
        SensorDeviceClass.TIMESTAMP
    )

    _attr_icon = (
        "mdi:clock-check-outline"
    )

    def __init__(
        self,
        coordinator: MudDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(
            coordinator,
            entry,
        )

        self._attr_unique_id = (
            f"{entry.entry_id}_last_refresh"
        )

        self._attr_name = (
            "Last Refresh"
        )

    @property
    def native_value(self):
        return self.coordinator.data.get(
            "retrieved_at"
        )
