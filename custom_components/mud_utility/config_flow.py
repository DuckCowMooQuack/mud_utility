"""Config flow for MUD Utilities."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from aiohttp import ClientError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.helpers.aiohttp_client import (
    async_get_clientsession,
)
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    MudApi,
    MudApiError,
    MudAuthError,
)
from .const import (
    CONF_GAS_CONTRACT,
    CONF_WATER_CONTRACT,
    DOMAIN,
)

_PASSWORD_SELECTOR = TextSelector(
    TextSelectorConfig(
        type=TextSelectorType.PASSWORD
    )
)


def _validate_contract_ids(
    user_input: dict[str, Any],
) -> dict[str, str]:
    """Return form errors for invalid contract IDs."""
    errors: dict[str, str] = {}

    for field in (
        CONF_GAS_CONTRACT,
        CONF_WATER_CONTRACT,
    ):
        value = user_input[field].strip()

        if not value.isdecimal():
            errors[field] = "invalid_contract"
            continue

        user_input[field] = value

    return errors


class MudUtilityConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a config flow for MUD Utilities."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate_contract_ids(
                user_input
            )

            if not errors:
                try:
                    await self._async_validate(
                        user_input
                    )

                except MudAuthError:
                    errors["base"] = "invalid_auth"

                except (
                    MudApiError,
                    ClientError,
                    TimeoutError,
                ):
                    errors["base"] = "cannot_connect"

                else:
                    await self.async_set_unique_id(
                        user_input[
                            CONF_USERNAME
                        ].lower()
                    )

                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title="MUD Utilities",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME
                    ): str,

                    vol.Required(
                        CONF_PASSWORD
                    ): _PASSWORD_SELECTOR,

                    vol.Required(
                        CONF_GAS_CONTRACT
                    ): str,

                    vol.Required(
                        CONF_WATER_CONTRACT
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, Any],
    ) -> ConfigFlowResult:
        """Start reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle reauthentication."""
        errors: dict[str, str] = {}

        entry = self._get_reauth_entry()

        if user_input is not None:
            updated_data = dict(entry.data)
            updated_data[CONF_PASSWORD] = (
                user_input[CONF_PASSWORD]
            )

            try:
                await self._async_validate(
                    updated_data
                )

            except MudAuthError:
                errors["base"] = "invalid_auth"

            except (
                MudApiError,
                ClientError,
                TimeoutError,
            ):
                errors["base"] = "cannot_connect"

            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_PASSWORD:
                            user_input[
                                CONF_PASSWORD
                            ]
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PASSWORD
                    ): _PASSWORD_SELECTOR
                }
            ),
            errors=errors,
        )

    async def _async_validate(
        self,
        data: Mapping[str, Any],
    ) -> None:
        """Validate credentials and contract IDs."""
        api = MudApi(
            async_get_clientsession(
                self.hass
            ),
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
            data[CONF_GAS_CONTRACT],
            data[CONF_WATER_CONTRACT],
        )

        await api.async_fetch_all()
