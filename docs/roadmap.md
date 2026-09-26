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

## Version 1.2: practice games and live cameras

- X01 practice games (301, 501, 701) on the local board: remaining score, busts, double out, checkout routes and the last 10 legs, with the `bust` and `leg_won` events.
- A practice panel in the live card with the checkout route and the bed to aim at next, and the practice controls in the automatic dashboard.
- Live camera streams from Board Manager 2 instead of snapshots.
- Camera state right after the detection starts or stops, instead of after the next poll.

## Version 1.3: matches, training games and statistics

- X01 matches for two to four players at one board: the turn passes when the darts are pulled, with legs, sets, player names and a scoreboard in the live card.
- Training games: Around the Clock, doubles training, checkout training and Bob's 27, with the target outlined on the board.
- Practice statistics: first-9 average, checkout rate, doubles rate and legs per day.
- Two blueprints: a practice caller and a highlight photo after a 180 or a checkout.

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
