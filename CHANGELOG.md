# Changelog

All notable changes of the Autodarts integration. The complete notes of every version, with each pull request, are on the [releases page](https://github.com/Dennis-Otto/ha-autodarts/releases); what comes next is in the [roadmap](docs/roadmap.md). Versions follow [Semantic Versioning](https://semver.org/).

## 1.5.0

- Shanghai, Halve-It and Killer for one to four players; X01 from 101 to 1001 with double in and a bull-off.
- Player profiles with statistics and personal bests per name, a match history, head-to-head records and a players card.
- A doubles analysis with the hit rate of every double, a doubles card and personal checkout routes.
- A caller in the scoreboard that announces the game through the browser, off by default.

## 1.4.0

- Cricket for one to four players with marks, closed numbers, points and marks per round, and a chalkboard in the live card.
- A scoreboard card and a full-screen scoreboard view for a screen at the board.
- Personal bests with an event when one is beaten, a training streak in days and a daily goal.
- `autodarts.start_game` starts X01, Cricket or a training game with players, names and format in one action.
- Detection quality: the share of corrected darts, with a repair that recalibrates the board when it rises.

## 1.3.0

- X01 matches for two to four players at one board, with legs, sets, player names and a scoreboard in the live card.
- Training games: Around the Clock, doubles training, checkout training and Bob's 27.
- Practice statistics: first-9 average, checkout rate, doubles rate and legs per day.
- Two blueprints: a practice caller and a highlight photo after a 180 or a checkout.

## 1.2.0

- X01 practice games (301, 501, 701): remaining score, busts, double out, checkout routes and the last 10 legs, with the `bust` and `leg_won` events.
- A practice panel in the live card with the checkout route and the next bed to aim at.
- Live camera streams from Board Manager 2 instead of snapshots.

## 1.1.0

- Training sessions that start with the first dart or on purpose, end after a pause and keep the last 20 sessions.
- The `session_started` and `session_ended` events, and a blueprint that ties light, detection and calibration to a session.
- The last visits in the live card, and the session state and past sessions in the training card.
- Board PC details from Board Manager 2: operating system, processor and detection software.

## 1.0.2

- The repository is now called `Dennis-Otto/ha-autodarts`; GitHub redirects the old address.

## 1.0.1

- Setup no longer offers the cloud link while Autodarts has not issued its client ID; old cloud entries keep working locally.
- Card colours accept valid CSS colours only.

## 1.0.0

- Local realtime connection to Board Manager 1 and 2, with automatic discovery; no Autodarts cloud account needed.
- Controls, board settings, camera health and Board Manager updates.
- Training analytics with hits per bed, a visit history and the `visit_completed` event.
- Three dashboard cards, an automatic dashboard and six blueprints.
- Documentation in English and German.

## 0.4.2 to 0.4.5

Pre-releases that led to 1.0.0.
