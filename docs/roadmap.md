# Roadmap

[← Documentation](README.md) · [Deutsch](de/roadmap.md)

This roadmap shows what is planned after version 1.0. It is a direction, not a promise: priorities follow feedback from players, and dates depend on spare time. Ideas and votes are welcome as [feature requests](https://github.com/Dennis-Otto/ha-autodarts/issues/new/choose).

## Version 1.0: the local foundation

Released features, all of them working without the Autodarts cloud:

- Local realtime connection to Board Manager 1 and 2, with automatic discovery.
- Controls, board settings, camera health and Board Manager updates.
- Training analytics with hits per bed, visit history and the `visit_completed` event.
- Three dashboard cards, an automatic dashboard and six blueprints.
- Documentation in English and German.

## Next: 1.1 and 1.2

| Topic | What it brings |
| --- | --- |
| **Training sessions** | Start and end a session explicitly, end it automatically after a period without darts, and keep a summary of past sessions. A blueprint ties light, detection and calibration to a session |
| **Local practice games** | An X01 practice mode that tracks the remaining score, recognises busts and suggests checkouts, all from the local board |
| **Live camera view** | Live streams of the board cameras instead of snapshots, where Board Manager 2 offers them |
| **Board PC details** | Operating system, hardware and vision software versions on the device page and in diagnostics |
| **Visits in the live card** | The last visits next to the current one |

## Later

| Topic | Dependency |
| --- | --- |
| **Cloud match events:** leg and match won, bust, player change, remaining score | An OAuth client ID from Autodarts, which has been requested |
| **HACS default repository** | Submitted in September 2026 ([hacs/default#11306](https://github.com/hacs/default/pull/11306)); the HACS review queue takes several months |
| **More languages** | Contributions from native speakers |
| **Protocol library on PyPI** | A separate library for the Board Manager protocol, a prerequisite for a possible Home Assistant core integration |

## How priorities are set

1. Anything that breaks for users, including changes in Board Manager versions, comes first.
2. Features that work locally come before cloud features.
3. Requests with the most reactions on GitHub come next.
