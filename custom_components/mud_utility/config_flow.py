"""Config flow for MUD Utilities."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
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
    CONF_UPDATE_INTERVAL_HOURS,
    CONF_WATER_CONTRACT,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
    MAX_UPDATE_INTERVAL_HOURS,
    MIN_UPDATE_INTERVAL_HOURS,
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
        value = str(user_input.get(field, "")).strip()
        user_input[field] = value

        if not value:
            continue

        if not value.isdecimal():
            errors[field] = "invalid_contract"

    if (
        not user_input[CONF_GAS_CONTRACT]
        and not user_input[CONF_WATER_CONTRACT]
    ):
        errors["base"] = "missing_contract"

    return errors


class MudUtilityConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a config flow for MUD Utilities."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        _config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return MudUtilityOptionsFlow()

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

                    vol.Optional(
                        CONF_GAS_CONTRACT,
                        default=""
                    ): str,

                    vol.Optional(
                        CONF_WATER_CONTRACT,
                        default=""
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
        session = async_create_clientsession(self.hass)
        try:
            api = MudApi(
                session,
                data[CONF_USERNAME],
                data[CONF_PASSWORD],
                data[CONF_GAS_CONTRACT],
                data[CONF_WATER_CONTRACT],
            )
            await api.async_fetch_all()
        finally:
            await session.close()


class MudUtilityOptionsFlow(config_entries.OptionsFlow):
    """Handle MUD Utilities options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL_HOURS,
                        default=self.config_entry.options.get(
                            CONF_UPDATE_INTERVAL_HOURS,
                            DEFAULT_UPDATE_INTERVAL_HOURS,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_UPDATE_INTERVAL_HOURS,
                            max=MAX_UPDATE_INTERVAL_HOURS,
                        ),
                    )
                }
            ),
        )
