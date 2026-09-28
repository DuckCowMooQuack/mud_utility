# MUD Utilities

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DuckCowMooQuack&repository=mud_utility&category=integration)

Custom Home Assistant integration for Metropolitan Utilities District customer portal consumption data.

This repository uses the Home Assistant domain `mud_utility`.

Repository: https://github.com/DuckCowMooQuack/mud_utility

## Features

- Adds gas and water consumption sensors from the M.U.D. customer portal.
- Imports billing-cycle gas and water history into Home Assistant long-term statistics.
- Supports UI setup and reauthentication.
- Polls the M.U.D. portal once per day.

## Installation

### HACS custom repository

Use the badge above or add the repository manually:

1. Open Home Assistant.
2. Open HACS.
3. Select the menu in the top-right corner.
4. Select **Custom repositories**.
5. Enter `https://github.com/DuckCowMooQuack/mud_utility`.
6. Select category `Integration`.
7. Select **Add**.
8. Open `MUD Utilities` in HACS.
9. Select **Download**.
10. Restart Home Assistant.
11. Go to **Settings > Devices & services**.
12. Select **Add integration**.
13. Search for `MUD Utilities`.
14. Enter your M.U.D. username, password, gas contract ID, and water contract ID.

### Manual

Copy this directory into Home Assistant:

```text
custom_components/mud_utility
```

After copying, restart Home Assistant and add `MUD Utilities` from the integrations UI.

## Configuration

You need:

- M.U.D. customer portal username or email.
- M.U.D. customer portal password.
- Gas contract ID.
- Water contract ID.

The contract IDs are visible in your M.U.D. account. They are not included in this repository and must be entered by each user during setup.

## Energy Dashboard

The integration imports M.U.D. billing-cycle history as long-term statistics, which the Energy Dashboard can use directly.

1. Go to **Settings > Dashboards > Energy**.
2. **Gas consumption:** select **Add gas source** and choose the statistic **MUD Utilities Gas Consumption**.
3. **Water consumption:** select **Add water source** and choose **MUD Utilities Water Consumption**.

Use the statistics rather than the `sensor.mud_*_consumption` entities. The sensors show the latest billing cycle, not a running total.

Gas is billed by M.U.D. in therms, which the Energy Dashboard does not accept as a gas unit. The gas statistic is therefore imported as energy in kWh (1 therm = 29.3001 kWh) and works as a gas source. This is an exact unit conversion and does not depend on M.U.D.'s monthly heat value or pressure factor. The `sensor.mud_gas_consumption` entity still reports therms, so it matches your bill.

If you use a static gas price in the Energy Dashboard, enter it per kWh. Divide your price per therm by 29.3001 (for example, $1.00 per therm is about $0.0341 per kWh).

## Plotly Examples

Optional Plotly Graph Card examples are available in `examples/plotly`.

These cards use the `billing_history` sensor attribute exposed by this integration and require the separate Plotly Graph Card custom card. Fresh installs should create entity IDs such as `sensor.mud_gas_consumption` and `sensor.mud_water_consumption`; adjust them if your Home Assistant instance creates different entity IDs.

## Privacy

This integration stores your M.U.D. username, password, and contract IDs in Home Assistant's config entry storage. Do not share diagnostics or configuration files that contain those values.

## Notes

This is an unofficial integration and is not affiliated with or endorsed by Metropolitan Utilities District.

The integration imports billing-cycle records into Home Assistant long-term statistics using statistic IDs such as `mud_utility:gas_consumption` and `mud_utility:water_consumption`.

The gas statistic is stored in kWh and the water statistic in CCF. If you upgrade from a version that stored gas in therms, the next refresh rewrites the gas history in kWh automatically.
