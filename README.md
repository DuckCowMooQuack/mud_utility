# MUD Utilities Test

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DuckCowMooQuack&repository=mud_utility_test&category=integration)

Custom Home Assistant integration for Metropolitan Utilities District customer portal consumption data.

This repository currently uses the test domain `mud_utility_test` so it can be installed beside an existing `mud_utility` integration without sharing entities or long-term statistic IDs.

Repository: https://github.com/DuckCowMooQuack/mud_utility_test

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
5. Enter `https://github.com/DuckCowMooQuack/mud_utility_test`.
6. Select category `Integration`.
7. Select **Add**.
8. Open `MUD Utilities Test` in HACS.
9. Select **Download**.
10. Restart Home Assistant.
11. Go to **Settings > Devices & services**.
12. Select **Add integration**.
13. Search for `MUD Utilities Test`.
14. Enter your M.U.D. username, password, gas contract ID, and water contract ID.

### Manual

Copy this directory into Home Assistant:

```text
custom_components/mud_utility_test
```

After copying, restart Home Assistant and add `MUD Utilities Test` from the integrations UI.

## Configuration

You need:

- M.U.D. customer portal username or email.
- M.U.D. customer portal password.
- Gas contract ID.
- Water contract ID.

The contract IDs are visible in your M.U.D. account. They are not included in this repository and must be entered by each user during setup.

## Plotly Examples

Optional Plotly Graph Card examples are available in `examples/plotly`.

These cards use the `billing_history` sensor attribute exposed by this integration and require the separate Plotly Graph Card custom card. Fresh installs should create test entity IDs such as `sensor.mud_utilities_test_gas_consumption` and `sensor.mud_utilities_test_water_consumption`; adjust them if your Home Assistant instance creates different entity IDs.

## Privacy

This integration stores your M.U.D. username, password, and contract IDs in Home Assistant's config entry storage. Do not share diagnostics or configuration files that contain those values.

## Notes

This is an unofficial integration and is not affiliated with or endorsed by Metropolitan Utilities District.

Before publishing a non-test release, rename the integration directory and manifest domain from `mud_utility_test` to the final public domain, such as `mud_utility`, and update the displayed name.
