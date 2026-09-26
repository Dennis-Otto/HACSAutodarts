# Security design

[← Documentation](README.md) · [Deutsch](de/sicherheit.md)

This page explains how the integration protects your data and your board, what it trusts, and which risks remain. Report vulnerabilities privately as described in [SECURITY.md](../SECURITY.md).

## What is protected

| Asset | Where it lives | Protection |
| --- | --- | --- |
| Board API key, TLS key, camera device paths | Board Manager configuration | Dropped as soon as a configuration is read; never stored, logged, shown or included in diagnostics |
| Autodarts OAuth tokens (optional cloud link) | Home Assistant config entry | Stored only there, refreshed automatically, never logged; the password is never seen |
| Board ID, board address, client ID | Home Assistant config entry | Redacted from diagnostics |
| Training session | Home Assistant `.storage` | Local only; deleted together with the integration |
| Control of the board | Board Manager API | Actions only on request of a user or an automation, sent once |

## Trust boundaries

```text
 Board PC                      Home Assistant                    Internet
┌────────────────────┐        ┌──────────────────────────┐       ┌──────────────────────┐
│ Board Manager      │  LAN   │ Autodarts integration    │ HTTPS │ Autodarts cloud      │
│ port 3180, no login├───────►│ validates every answer   ├──────►│ (optional, OAuth)    │
└────────────────────┘        │ dashboard cards (browser)│       │ discovery service    │
                              └──────────────────────────┘       │ (only when searched) │
                                                                 └──────────────────────┘
```

1. **Board Manager → integration.** The local API has no login. The integration treats every answer as untrusted input: types, ranges and structures are checked before any value reaches an entity, and unexpected data reads as *unknown* instead of raising errors.
2. **Integration → dashboard.** The cards render board data in the browser. Every text from the board or the entity registry is escaped, and numbers are validated before they become SVG geometry.
3. **Integration → internet.** Nothing leaves the local network in local mode. *Search for boards* contacts the public Autodarts discovery service once, on request. The optional cloud link uses the OAuth device login over HTTPS through Home Assistant's shared session.

## Threats and countermeasures

| Threat | Countermeasure | Evidence |
| --- | --- | --- |
| Secrets from the board leak into Home Assistant | Configuration is reduced to an allow-list of fields right after reading; responses to writes are discarded | Tests check that the API key never appears in entities, diagnostics or logs, also in the Docker end-to-end test |
| Malformed or hostile board data crashes the integration or the cards | Validation of every payload; property-based tests with Hypothesis (training engine) and fast-check (cards) run thousands of random inputs | `tests/test_training_properties.py`, `tests/frontend/properties.test.js` |
| Script injection through board or device names in the cards | All inserted text is escaped; no `innerHTML` with unescaped data | fast-check property "escaped text never contains markup" |
| A wrong board at a configured address shows or controls foreign data | The board ID is checked on every read; a mismatch makes the entities unavailable and raises a repair notice | `tests/test_quality.py` |
| An action runs twice, for example a restart or a reset | Actions are sent once and never retried automatically | `tests/test_local_api.py` |
| A compromised dependency or build | Hash-pinned dependencies, pinned Actions and images, Dependabot, dependency review, CodeQL, Gitleaks, OpenSSF Scorecard | [Development](development.md#continuous-integration) |
| A tampered release | Release packages carry Sigstore-signed SLSA provenance | [Releases](releases.md#signed-release-packages) |

## Design principles

- **Least privilege:** GitHub workflows run with read-only tokens unless a job needs more; the integration only reads the Board Manager and writes to it only when you or an automation ask for it.
- **Fail safe:** unknown data becomes *unknown*, an unreachable board makes entities unavailable, and a wrong board never shows its data.
- **Local first:** the cloud is optional, and local control never depends on it.
- **Small attack surface:** no Python dependencies at runtime, no open ports, no services beyond the entities.

## Residual risks

- The Board Manager's local API has no login. Anyone who can reach port 3180 in your network can control the board, with or without this integration. Keep the board PC in a trusted network.
- The local API is not officially supported by Autodarts from Board Manager 2 on. A future Board Manager version may change it; the integration detects the generation and is tested against both.
