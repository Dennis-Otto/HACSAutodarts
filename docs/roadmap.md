# Roadmap

[← Documentation](README.md) · [Deutsch](de/roadmap.md)

This roadmap shows what each version brought and what comes next. It is a direction, not a promise: priorities follow feedback from players, and dates depend on spare time. Ideas and votes are welcome as [feature requests](https://github.com/Dennis-Otto/ha-autodarts/issues/new/choose).

## Version 1.0: the local foundation

Released features, all of them working without the Autodarts cloud:

- Local realtime connection to Board Manager 1 and 2, with automatic discovery.
- Controls, board settings, camera health and Board Manager updates.
- Training analytics with hits per bed, visit history and the `visit_completed` event.
- Three dashboard cards, an automatic dashboard and six blueprints.
- Documentation in English and German.

## Version 1.1: training sessions

- Training sessions that start with the first dart or on purpose, end after a pause and keep a summary of the last 20 sessions.
- The `session_started` and `session_ended` events, and a seventh blueprint that ties light, detection and calibration to a session.
- The last visits in the live card, the session state and past sessions in the training card.
- Board PC details from Board Manager 2: operating system, processor and detection software.

## Next: 1.2

| Topic | What it brings |
| --- | --- |
| **Local practice games** | An X01 practice mode that tracks the remaining score, recognises busts and suggests checkouts, all from the local board |
| **Live camera view** | Live streams of the board cameras instead of snapshots, where Board Manager 2 offers them |

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
