# Autodarts for Home Assistant — WIP

<img src="custom_components/autodarts/brand/icon.png" alt="Autodarts" width="80" height="80">

> **Work in progress.** Local Board Manager control works without a client ID. Local reads have been verified with Board Manager 1.0.7; control actions and dart events still require hardware validation. Cloud account linking requires an approved project client ID and has not yet been validated with a live account.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![CI](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/tests.yml/badge.svg)](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/tests.yml)
[![Docker E2E](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/e2e.yml/badge.svg)](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/e2e.yml)
[![Secret scan](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/secret-scan.yml)
[![CodeQL](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/codeql.yml/badge.svg)](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/codeql.yml)
[![SBOM](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/sbom.yml/badge.svg)](https://github.com/Dennis-Otto/HACSAutodarts/actions/workflows/sbom.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Dennis-Otto/HACSAutodarts/badge)](https://scorecard.dev/viewer/?uri=github.com/Dennis-Otto/HACSAutodarts)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/14935/badge)](https://www.bestpractices.dev/projects/14935)

A [Home Assistant](https://www.home-assistant.io/) custom integration for [Autodarts](https://autodarts.io/) — the automatic dart scoring system.

This fork of [Trkal/HACSAutodarts](https://github.com/Trkal/HACSAutodarts) uses the new Autodarts **device-link login**: Home Assistant displays an 8-character code, you approve it in your browser, and setup continues automatically. It supports local board control on its own, plus optional cloud match data. Local control keeps working when Home Assistant’s cloud credentials expire.

> **Cloud setup requirement:** A public OAuth client ID approved for this integration with device authorization enabled is required. No project client ID is bundled yet, and the old `autodarts-play` client does not support the new login flow. Without a valid client ID, cloud account linking cannot be completed. **Local setup does not require this ID.** See the [German setup instructions](docs/SETUP-DE.md).

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

### Local board control (no integration client ID needed)

- **Buttons:** start/stop detection, reset detection, restart Board Manager, start automatic calibration for all cameras or an individual camera, reset local training statistics.
- **Additional buttons, disabled by default:** connect/disconnect the board’s cloud connection, start/stop camera streams.
- **Switches:** detection, board cloud connection, calibration on start, automatic recalibration, automatic distortion correction.
- **Select:** camera standby after 5, 10, 15, 30 or 60 minutes.
- **Sensors:** local connectivity, detection status/event, last segment, number of detected darts, last dart score and sum of detected darts.
- **Optional diagnostics:** detection/camera FPS and one snapshot camera per configured camera, disabled by default.
- **Realtime events:** detected/corrected darts, takeout start/finish and status changes as a native HA event entity, with WebSocket reconnect and HTTP fallback.
- **Detection states:** hand detected, stable image, partial/full takeout, cameras active and calibration in progress.
- **Camera health:** per-camera and combined problem sensors after 15 seconds of zero FPS during active detection; normal stops, calibration and standby are excluded.
- **Persistent local training session:** observed darts, triples, bull hits, 180s, points and session start, with a reset button. Current-visit corrections adjust counts; startup/reconnection snapshots are not replayed as new darts. No player assignment or game rules are inferred.
- Local reads every 2 seconds complement immediate push updates; settings and firmware version every 30 seconds. Actions request a refresh.

See [local setup, controls and examples (German)](docs/LOCAL-CONTROL.md).

## Requirements

For **local control**: an already configured Autodarts Board Manager reachable from Home Assistant on the local network (default port **3180**). No separate cloud login, password or client ID is needed in this integration. Board Manager’s own registration and connection to Autodarts remain separate.

For **cloud match sensors**, additionally: an Autodarts account with access to the board and a public OAuth client ID registered for this integration with device authorization enabled. No client secret or redirect URI is required.

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

### Integration icon

Version 0.4.1 bundles the Autodarts icon and light/dark logos, including high-resolution versions. Home Assistant **2026.3 or newer** loads these directly from the integration, including for local-only setups without a client ID. After updating, restart Home Assistant and refresh the browser/app if an old placeholder remains. See [Home Assistant's local brand image support](https://developers.home-assistant.io/docs/core/integration/brand_images/).

The HACS repository list may still show a placeholder: its current frontend uses the central Home Assistant brands server rather than bundled images. The local assets apply to Home Assistant's integration UI. [Asset sources and rendering instructions](docs/branding/README.md).

## Configuration

Choose **Local board** in **Settings → Devices & Services → Add Integration → Autodarts**. Enter the IP/hostname without `http://` or a port, and enter the port separately (normally `3180`). The board ID is read automatically. No Autodarts credentials are stored for this mode.

To add cloud access later, choose **Reconfigure → Link cloud account** on the existing integration. Its board and entity IDs are retained.

For cloud setup:

1. Choose **Link cloud account** in the integration setup menu.
2. Enter the registered **Autodarts client ID**, and optionally your local board IP/port.
3. Home Assistant shows a code such as `ABCD-EFGH` and a direct login link.
4. Open the displayed link, or visit `https://auth.autodarts.io/link` on another device and enter the code. Sign in and approve the connection.
5. Home Assistant waits for approval automatically. If you have several boards, choose one.

No passwords or redirect URLs are entered into Home Assistant. Device-code expiry and denied requests offer a new login attempt. Polling follows the server's interval and `slow_down` responses; cancelling setup stops polling.

Access tokens refresh through `/auth/v1/refresh`. Rotated refresh tokens are saved immediately, including when a subsequent cloud request fails. Revoked or expired credentials trigger Home Assistant's reauthentication flow.

### Updating an existing installation

The fork uses the same `autodarts` integration domain as the original, so only one can be installed at a time. Change the HACS repository supplying the integration to this fork, or replace only `config/custom_components/autodarts` manually, then restart Home Assistant. Keep the existing integration entry in **Devices & Services**.

Existing version-2 entries using the old Keycloak flow ask you to **re-authenticate**. If a local host is configured, local controls remain available while cloud login is pending. To add or update the local address, use **Reconfigure → Local board** on the existing entry. Enter the registered client ID and approve the new code using the account that owns the existing board. The entry, board ID, sensor unique IDs and local connection settings are retained. Linking an account without the original board is rejected instead of switching boards.

## Validation

Automated tests use **Home Assistant 2026.9.2 / Python 3.14**, with mocked Autodarts HTTP responses. They cover device approval, polling/backoff, denial/expiry/cancellation, board selection, reauthentication, refresh-token rotation, local onboarding/upgrading, entity services, partial settings updates, command errors, connectivity recovery operation during cloud failures, push/poll races, reconnect/cancellation, camera failure thresholds and training persistence/corrections. Earlier Home Assistant versions have not been validated.

Local status, version, sanitized settings, FPS, motion and camera state reads, and WebSocket connection handling have been verified with Board Manager 1.0.7. Hardware validation of control actions and dart sequences, and live validation of cloud login and match data, are still pending.

```sh
python3.14 -m venv .venv
.venv/bin/pip install -r requirements-test.txt
.venv/bin/pytest -q
.venv/bin/ruff check custom_components tests
```

The [Docker end-to-end test](tests/e2e/README.md) starts a real Home Assistant
2026.9.3 container with this integration and a simulated Board Manager. It covers
onboarding, local setup, entity services, realtime dart events, diagnostics and
removal. It requires Docker with Compose:

```sh
bash tests/e2e/run.sh
```

Dependabot checks Python dependencies, GitHub Actions and the Home Assistant image
of the Docker end-to-end test weekly on Monday mornings
(Europe/Berlin). Patch and minor updates are grouped and automatically squash-merged
after all required checks pass. Major updates remain separate pull requests for
manual review. Repository auto-merge and required checks are enforced through the
repository settings and main-branch ruleset. Merged dependency updates automatically
produce a checked maintenance release with a new patch version and changelog,
including test dependencies and GitHub Actions updates. Major dependency updates
enter the same release process after a maintainer merges them. This does not install
updates into Home Assistant automatically.

Pull requests are checked with pytest, Ruff, the Docker end-to-end test, HACS
validation, Home Assistant hassfest, workflow linting, Python CodeQL analysis,
dependency vulnerability review, Gitleaks and an SPDX SBOM. HACS/hassfest, CodeQL
and the SBOM also run weekly to detect changes in platform requirements and security
checks. OpenSSF Scorecard evaluates the repository's supply-chain security on every
push to `main` and weekly. GitHub Actions are pinned to commit hashes or container
digests and maintained by Dependabot.

## Releases and changelogs

The **Release integration** workflow generates categorized release notes for the
HACS/Home Assistant update dialog. An optional introduction appears above the
automatic changelog. It verifies that the version matches `manifest.json` and can
save a draft or publish a stable/prerelease version. **Release dependency updates**
automatically prepares and publishes maintenance versions after Dependabot merges,
with a scheduled fallback every 30 minutes. It retains the latest release's channel:
WIP updates require the repository's prerelease switch in HACS to be enabled.
See the [release guide](docs/releases.md).

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
| Board Manager connection | Local | HTTP reachability, independent of cloud connection | — |
| Local detection status | Local | Board Manager status | — |
| Last throw score | Local | Segment number × multiplier | points |
| Detected visit score | Local | Sum of detected darts, without game rules such as bust | points |
| Detection / camera frame rate | Local | Optional performance diagnostics | fps |

## Automations

Use these sensors to trigger Home Assistant automations, for example:

- Flash lights when a player checks out (match state changes to "Finished")
- Play a sound when a 180 is scored (visit score = 180)
- Send a notification with match results
- Display live scores on a dashboard

## Contributing and security

Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md) for requirements
and checks. Use [SUPPORT.md](SUPPORT.md) for bug reports and questions. Report
suspected vulnerabilities privately as described in [SECURITY.md](SECURITY.md), never
in a public issue. Participation follows the [code of conduct](CODE_OF_CONDUCT.md)
and the project's [governance](GOVERNANCE.md).

## License

MIT

Autodarts and Winmau names and brand artwork belong to their respective owners. The bundled brand assets identify the supported product; they are not covered by the integration's MIT license. This is an unofficial community integration.
