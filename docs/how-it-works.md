# How it works

[← Documentation](README.md) · [Deutsch](de/funktionsweise.md)

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="images/en/architecture-dark.png">
  <img src="images/en/architecture-light.png" alt="Architecture: the Board Manager on the board PC sends realtime events to the Autodarts integration in Home Assistant, which reads and controls the board over HTTP, keeps the training session locally and provides entities, board events, cards and automations; the Autodarts cloud optionally adds match data." width="560">
</picture>

A board is one config entry with up to two independent connections:

- **Local** (recommended): directly to the Board Manager in your network. It needs no login and provides controls, realtime events and training.
- **Cloud** (optional): match data from Autodarts. If it fails, local control keeps working, and the other way round.

## Data updates

| Source | How | Interval |
| --- | --- | --- |
| Board state, dart positions, motion, cameras, frame rates | WebSocket `/api/events` of the Board Manager | Immediately |
| Reconciliation while realtime events arrive | HTTP read | Every 30 seconds |
| Fallback without realtime events | HTTP read | Every 2 seconds |
| Board Manager 2 | One combined read of `/api/system` per interval | As above |
| Board Manager 1 settings and version | HTTP read | Every 30 seconds, and after every action |
| Cloud match data | Autodarts API | Every 5 seconds |

Further details:

- **Reconnects.** If the realtime connection drops, the integration switches to fast polling at once. It then reconnects with a back-off of 1 to 60 seconds.
- **No stale overwrites.** A slow HTTP read never overwrites a newer realtime message.
- **Short hiccups.** A single missed read while realtime events still arrive is not treated as an outage.
- **After an action.** The integration reads the board immediately after every action, so a switch reflects the new state within about a second.

## Board Manager generations

| | Board Manager 1 (classic app) | Board Manager 2 (headless) |
| --- | --- | --- |
| Detection | Version starts with `1.` | Version starts with `2.` and `/api/system` exists |
| Reads | Separate reads for state, statistics, cameras, motion, settings and version | One combined `/api/system` read |
| Extras | Board cloud link switch | Cloud connection, CPU, memory, update notice, mDNS discovery |

The generation is detected on every read. When you update the board, the integration reloads itself and adds or removes the generation-specific entities; nothing else changes. While a board still runs Board Manager 1, a repair notice recommends the update.

## Training session

The training session is computed in Home Assistant from what the board detects. It follows these rules:

- **Darts count once.** Repeated messages, camera jitter of the position and reconnects never count a dart twice.
- **Corrections revise.** If the board corrects a dart in the current visit, the totals follow the correction, for example when a 180 turns into a 140.
- **Takeouts end a visit.** Removing darts ends the visit; the removed darts keep their score. The same happens when new darts appear without an empty board in between (a missed takeout), and when the detection stops.
- **Startup darts are ignored.** Darts that are already on the board when Home Assistant or the connection starts are not counted.
- **Withdrawn detections.** If the board withdraws a detection outside a takeout, the dart is removed from the totals again.
- **Visit buckets.** 100+ counts visits with 100–139 points, 140+ with 140–179, and 180 with exactly three triple 20s. Merged visits with more than three darts (after a missed takeout) are not bucketed.
- **Storage.** The session is saved in Home Assistant's `.storage` folder at most every five seconds, and on shutdown. It is deleted together with the integration.

The session does not know players or games. It counts every detected dart, regardless of whether you play X01, Cricket or just practise.

## Camera health

A camera counts as failed when it delivers no frames for **15 seconds** while the detection runs. Stopped detection, calibration and camera standby are not failures. The combined *Camera problem* sensor is on when any camera has failed.

## Privacy

- **Local mode** talks only to the Board Manager in your network. Nothing is sent to the internet.
- **Search for boards** asks `discover.autodarts.com`, the public Autodarts discovery service, once when you use it. The service sees your public IP address and returns the boards registered from it.
- **The optional cloud link** uses the Autodarts device login. Home Assistant stores OAuth tokens, never your password.
- **Board secrets** are dropped as soon as they are read and are never stored, logged or shown: the board API key, TLS keys, camera device paths and similar configuration.
- **Diagnostics** redact the board ID, host, client ID and tokens.

## Security

- The Board Manager's local API does not ask for a login, so anyone who can reach port 3180 in your network can use it, with or without Home Assistant. Keep the board PC in a trusted network.
- Actions are only sent when you or an automation trigger them. They are never repeated automatically.
