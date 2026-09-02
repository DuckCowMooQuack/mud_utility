"""Async client for the M.U.D. customer portal."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urljoin

from aiohttp import ClientSession, ClientTimeout

from .const import BASE_URL, LOGIN_URL

_TIMEOUT = ClientTimeout(total=30)


class MudApiError(Exception):
    """Base M.U.D. API error."""


class MudAuthError(MudApiError):
    """Raised when M.U.D. authentication fails."""


class MudApi:
    """Client for M.U.D. portal data."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        gas_contract: str,
        water_contract: str,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._gas_contract = gas_contract
        self._water_contract = water_contract

    async def async_login(self) -> None:
        """Create an authenticated SAP session."""
        async with self._session.get(
            LOGIN_URL,
            params={
                "sap-client": "500",
                "sap-language": "EN",
            },
            timeout=_TIMEOUT,
        ) as response:
            if response.status >= 400:
                raise MudApiError(
                    "Initial M.U.D. login page returned "
                    f"HTTP {response.status}"
                )

        payload = [
            ("sap-system-login-oninputprocessing", ""),
            ("sap-urlscheme", ""),
            ("sap-system-login", "onLogin"),
            ("sap-system-login-basic_auth", ""),
            ("sap-client", "500"),
            ("sap-language", "EN"),
            ("sap-accessibility", ""),
            ("sap-system-login-cookie_disabled", ""),
            ("sap-hash", ""),
            ("sap-alias", self._username),
            ("sap-password", self._password),
            ("sap-language", "EN"),
        ]

        async with self._session.post(
            LOGIN_URL,
            data=payload,
            headers={
                "Referer": LOGIN_URL,
                "Origin": BASE_URL,
            },
            allow_redirects=False,
            timeout=_TIMEOUT,
        ) as response:
            if response.status not in (301, 302, 303):
                raise MudAuthError(
                    "M.U.D. login did not return the expected "
                    f"redirect (HTTP {response.status})"
                )

    async def async_fetch_all(self) -> dict[str, Any]:
        """Log in once and fetch full gas and water history."""
        await self.async_login()

        gas = await self._async_get_consumption(
            "gas",
            self._gas_contract,
        )

        water = await self._async_get_consumption(
            "water",
            self._water_contract,
        )

        return {
            "retrieved_at": datetime.now(timezone.utc),
            "gas": gas,
            "water": water,
        }

    async def _async_get_consumption(
        self,
        utility: str,
        contract_id: str,
    ) -> dict[str, Any]:
        """Fetch billing-cycle consumption history."""
        contract_key = quote(contract_id, safe="")

        url = (
            f"{BASE_URL}/sap/opu/odata/sap/"
            "ZUTE_ERP_UT_UMC_SRV/"
            f"Contracts('{contract_key}')/"
            "ContractConsumptionValues"
        )

        params = {
            "$filter": ("ConsumptionPeriodTypeID eq 'BC'"),
            "$expand": "MeterReadingCategory",
            "$format": "json",
        }

        rows: list[dict[str, Any]] = []
        next_url: str | None = url
        next_params: dict[str, str] | None = params

        while next_url is not None:
            async with self._session.get(
                next_url,
                params=next_params,
                headers={
                    "Accept": "application/json",
                    "DataServiceVersion": "2.0",
                    "MaxDataServiceVersion": "2.0",
                },
                timeout=_TIMEOUT,
            ) as response:
                if response.status in (401, 403):
                    raise MudAuthError(
                        f"M.U.D. rejected the authenticated "
                        f"{utility} request "
                        f"(HTTP {response.status})"
                    )

                if response.status >= 400:
                    body = (await response.text())[:300]

                    raise MudApiError(
                        f"M.U.D. {utility} request returned "
                        f"HTTP {response.status}: {body}"
                    )

                try:
                    payload = await response.json(
                        content_type=None
                    )
                    page = payload["d"]
                    rows.extend(page["results"])

                except (
                    ValueError,
                    KeyError,
                    TypeError,
                ) as err:
                    raise MudApiError(
                        "Unexpected M.U.D. response "
                        f"format for {utility}"
                    ) from err

            next_page = page.get("__next")
            next_url = (
                urljoin(BASE_URL, next_page)
                if isinstance(next_page, str)
                else None
            )
            next_params = None

        if not rows:
            raise MudApiError(
                f"M.U.D. returned no {utility} "
                "consumption records"
            )

        history = [
            self._normalize_row(row)
            for row in rows
        ]

        history.sort(
            key=self._record_sort_key
        )

        latest = history[-1]

        return {
            "contract_id": contract_id,
            "records_returned": len(history),
            "latest": latest,
            "history": history,
        }

    def _normalize_row(
        self,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        """Normalize one M.U.D. billing-cycle record."""
        raw_value = row.get("ConsumptionValue")

        try:
            consumption = float(raw_value)
        except (TypeError, ValueError):
            consumption = raw_value

        raw_billed = row.get("BilledAmount")

        try:
            billed_amount = float(raw_billed)
        except (TypeError, ValueError):
            billed_amount = raw_billed

        year = str(
            row.get("BillingPeriodYear", "")
        ).strip()

        month = str(
            row.get("BillingPeriodMonth", "")
        ).strip()

        billing_period = None

        if year and month:
            try:
                billing_period = (
                    f"{int(year):04d}-"
                    f"{int(month):02d}"
                )
            except ValueError:
                billing_period = (
                    f"{year}-{month}"
                )

        reading_category = row.get(
            "MeterReadingCategory"
        )

        category_description = None

        if isinstance(
            reading_category,
            dict,
        ):
            category_description = (
                reading_category.get(
                    "Description"
                )
            )

        return {
            "period_start":
                self._parse_sap_date(
                    row.get("StartDate")
                ),
            "period_end":
                self._parse_sap_date(
                    row.get("EndDate")
                ),
            "billing_period":
                billing_period,
            "consumption":
                consumption,
            "unit":
                row.get("ConsumptionUnit"),
            "billed_amount":
                billed_amount,
            "currency":
                row.get("Currency"),
            "period_type":
                row.get(
                    "ConsumptionPeriodTypeID"
                ),
            "reading_category_id":
                row.get(
                    "MeterReadingCategoryID"
                ),
            "reading_category":
                category_description,
        }

    @staticmethod
    def _record_sort_key(
        record: dict[str, Any],
    ) -> datetime:
        """Sort by actual meter period, not billing-month label."""
        return (
            record.get("period_end")
            or record.get("period_start")
            or datetime.min.replace(
                tzinfo=timezone.utc
            )
        )

    @staticmethod
    def _parse_sap_date(
        value: Any,
    ) -> datetime | None:
        """Convert SAP /Date(milliseconds)/ values to UTC."""
        if not value:
            return None

        if not isinstance(value, str):
            return None

        match = re.fullmatch(
            r"/Date\((-?\d+)"
            r"(?:[+-]\d{4})?\)/",
            value,
        )

        if not match:
            return None

        try:
            milliseconds = int(
                match.group(1)
            )

            return datetime.fromtimestamp(
                milliseconds / 1000,
                tz=timezone.utc,
            )

        except (
            ValueError,
            OSError,
            OverflowError,
        ):
            return None
