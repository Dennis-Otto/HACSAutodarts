# Autodarts for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

A [Home Assistant](https://www.home-assistant.io/) custom integration for [Autodarts](https://autodarts.io/) — the automatic dart scoring system.

This fork of [Trkal/HACSAutodarts](https://github.com/Trkal/HACSAutodarts) uses the new Autodarts **device-link login**: Home Assistant displays an 8-character code, you approve it in your browser, and setup continues automatically. It retrieves cloud match data and board status, with an optional local connection for throw detection.

> **Cloud setup requirement:** A public OAuth client ID approved for this integration with device authorization enabled is required. No project client ID is bundled yet, and the old `autodarts-play` client does not support the new login flow. Without a valid client ID, cloud account linking cannot be completed. See the [German setup instructions](docs/SETUP-DE.md).

The device-link implementation follows the [Autodarts authentication migration guide](https://gist.github.com/lloydowen/960079f2b518f6f5d68e160465298964).

## Features

### Board Sensors
- **Board Status** — connected / disconnected
- **Board Event** — last detection event (Throw, Takeout, Starting)

### Match Sensors
- **Game Mode** — X01, Cricket, Count Up, etc.
- **Match State** — Active / Finished / No match
- **Round** — current round number
- **Visit Score** — points scored in the current turn
- **Total Turns** — total turns played in the match

### Detection Sensors (requires local board IP)
- **Last Throw** — segment hit (e.g. T20, D16, S5, Bull)
- **Throws in Turn** — number of darts thrown in the current turn (0–3)

## Requirements

- An **Autodarts account**
- A public OAuth client ID registered for this integration, with **device authorization enabled** (no client secret or redirect URI required)
- At least one board registered to your account
- *(Optional)* Local network access to the board for throw detection (default port: **3180**)

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Go to **Integrations** → click the **three dots** menu → **Custom repositories**
3. Add `https://github.com/Dennis-Otto/HACSAutodarts` as an **Integration**
4. Search for **Autodarts** and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/autodarts` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration → Autodarts**.
2. Enter the registered **Autodarts client ID**, and optionally your local board IP/port.
3. Home Assistant shows a code such as `ABCD-EFGH` and a direct login link.
4. Open the displayed link, or visit `https://auth.autodarts.io/link` on another device and enter the code. Sign in and approve the connection.
5. Home Assistant waits for approval automatically. If you have several boards, choose one.

No passwords or redirect URLs are entered into Home Assistant. Device-code expiry and denied requests offer a new login attempt. Polling follows the server's interval and `slow_down` responses; cancelling setup stops polling.

Access tokens refresh through `/auth/v1/refresh`. Rotated refresh tokens are saved immediately, including when a subsequent cloud request fails. Revoked or expired credentials trigger Home Assistant's reauthentication flow.

### Updating an existing installation

The fork uses the same `autodarts` integration domain as the original, so only one can be installed at a time. Change the HACS repository supplying the integration to this fork, or replace only `config/custom_components/autodarts` manually, then restart Home Assistant. Keep the existing integration entry in **Devices & Services**.

Existing version-2 entries using the old Keycloak flow ask you to **re-authenticate**. Enter the registered client ID and approve the new code using the account that owns the existing board. The entry, board ID, sensor unique IDs and local connection settings are retained. Linking an account without the original board is rejected instead of switching boards.

## Validation

Automated tests use **Home Assistant 2026.9.2 / Python 3.14**, with mocked Autodarts HTTP responses. They cover device approval, polling/backoff, denial/expiry/cancellation, board selection, reauthentication, refresh-token rotation, concurrent requests and integration setup/sensors. Earlier Home Assistant versions have not been validated.

**A successful live account login and real-board session have not been tested**, because a registered client ID is still required.

```sh
python3.14 -m venv .venv
.venv/bin/pip install -r requirements-test.txt
.venv/bin/pytest -q
.venv/bin/ruff check custom_components/autodarts/api.py custom_components/autodarts/config_flow.py custom_components/autodarts/__init__.py custom_components/autodarts/coordinator.py custom_components/autodarts/const.py tests
```

## Sensors

| Sensor | Source | Description | Unit |
|--------|--------|-------------|------|
| Board Status | Cloud | Board connection state | — |
| Board Event | Local/Cloud | Last detection event | — |
| Game Mode | Cloud | Active game type (X01, Cricket, etc.) | — |
| Match State | Cloud | Match status (Active/Finished/No match) | — |
| Round | Cloud | Current round number | — |
| Last Throw | Local | Last dart segment (e.g. T20, D16) | — |
| Throws in Turn | Local | Darts thrown this turn (0–3) | darts |
| Visit Score | Cloud | Points scored in current turn | points |
| Total Turns | Cloud | Total turns in the match | turns |

## Automations

Use these sensors to trigger Home Assistant automations, for example:

- Flash lights when a player checks out (match state changes to "Finished")
- Play a sound when a 180 is scored (visit score = 180)
- Send a notification with match results
- Display live scores on a dashboard

## License

MIT
