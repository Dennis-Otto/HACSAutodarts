# Entities and events

[← Documentation](README.md) · [Deutsch](de/entitaeten.md)

Every board is one device with the entities below. Their names follow your Home Assistant language, and their entity IDs are derived from the board name, for example `sensor.autodarts_board_training_3_dart_average`.

**Legend:**

| Column or mark | Meaning |
| --- | --- |
| **BM** | The Board Manager generation that provides the entity: 1, 2 or both |
| *Disabled* | Created disabled; enable it in the entity settings if you need it |
| *Diagnostic*, *Configuration* | The entity category; these entities are grouped separately on the device page |

<img src="images/en/device.png" alt="Device page of an Autodarts board in Home Assistant" width="760">

## Live visit

| Entity | Type | Description |
| --- | --- | --- |
| Detection status | Sensor (enum) | `offline`, `starting`, `stopping`, `stopped`, `throw` (ready), `takeout`, `takeout_in_progress`, `calibrating`, `error`. Unknown statuses of future Board Manager versions read as *unknown*. |
| Last dart | Sensor | Segment of the last dart, for example `T20`, `D16`, `S5`, `25`, `Bull`. |
| Last dart score | Sensor, points | Score of the last dart. |
| Darts in visit | Sensor, darts | Darts currently detected on the board (0–3). |
| Detected visit score | Sensor, points | Sum of the detected darts. The `throws` attribute lists each dart with `segment`, `number`, `multiplier`, `score`, `bed` and the normalised position `x`/`y`. The recorder does not store `throws`. |
| Last board event | Sensor | The Board Manager's latest event text, such as `Throw detected` or `Takeout started`. |

The visit score is the plain sum of the darts, without game rules such as busts.

## Board events

The **Board events** entity (`event.*_board_events`) fires native Home Assistant events. Its `event_type` attribute tells what happened, and further attributes carry the details. Every event also has `source`: `websocket` for realtime events, or `poll` when it was noticed during a reconciliation read.

| `event_type` | When | Attributes |
| --- | --- | --- |
| `dart_detected` | A new dart lands | `dart_index` (1–3), `segment`, `score` |
| `dart_corrected` | The board corrects a detected dart | `dart_index`, `segment`, `score` |
| `takeout_started` | You start pulling the darts | none |
| `takeout_finished` | The board is clear again | none |
| `visit_completed` | A visit ends: on takeout, when new darts follow a missed takeout, or when detection stops | `score`, `darts`, `segments` (for example `["T20", "T20", "S20"]`) |
| `status_changed` | The detection status changes | `status` |

Events are never replayed after a restart or reconnection. See [automations](automations.md) for examples.

## Training session

The integration keeps a training session of all darts the board detects, in Home Assistant, independent of Autodarts games. It survives restarts and runs until you reset it with **Reset training statistics** or the *New session* button of the [training card](cards.md#training-card).

| Entity | Type | Description |
| --- | --- | --- |
| Training darts | Sensor, total | Darts in the session. The `hits` attribute counts the hits per bed, for example `{"T20": 12, "S20": 30, "BULL": 2, "MISS": 3}`; the heatmap uses it. The recorder does not store `hits`. |
| Training points | Sensor, total | Sum of all dart scores. |
| Training 3-dart average | Sensor | Points per three darts, the usual darts average. *Unknown* before the first dart. |
| Training visits | Sensor, total | Visits with at least one counted dart. |
| Training highest visit | Sensor | Highest visit score of the session. |
| Training 100+ visits | Sensor, total | Visits with 100–139 points. |
| Training 140+ visits | Sensor, total | Visits with 140–179 points. |
| Training 180s | Sensor, total | Visits with three triple 20s. |
| Training triples | Sensor, total | Darts in a triple bed. |
| Training doubles | Sensor, total | Darts in a double bed (bull excluded). |
| Training bull hits | Sensor, total | Darts in the bull or outer bull. |
| Training misses | Sensor, total | Darts outside the scoring area. |
| Training session start | Sensor, timestamp | When the session started. |
| Reset training statistics | Button | Starts a new session. The board itself is not touched. |

Totals use the state class *total increasing*, so Home Assistant's statistics and energy-style graphs handle resets correctly. [How the counting works](how-it-works.md#training-session).

## Controls

| Entity | Type | Description |
| --- | --- | --- |
| Detection | Switch | Starts or stops the dart detection. |
| Start detection, Stop detection | Buttons | The same actions as buttons, for scripts and dashboards. |
| Reset detection | Button | Discards the darts detected on the board. |
| Start automatic calibration | Button, *Configuration* | Calibrates all cameras. |
| Calibrate camera *N* | Button, *Configuration* | Calibrates one camera. |
| Restart Board Manager | Button, *Configuration* | Restarts the Board Manager service. |
| Start camera streams, Stop camera streams | Buttons, *Configuration*, *Disabled* | Controls the camera streams of the Board Manager. |
| Board cloud link | Switch, **BM 1** | Connects or disconnects the board's own connection to Autodarts. |
| Connect board cloud link, Disconnect board cloud link | Buttons, **BM 1**, *Disabled* | The same as buttons. |

Every action is sent **once**. If the board rejects it or does not answer, Home Assistant shows an error message instead of retrying, so an action is never executed twice.

## Board settings

| Entity | Type | Description |
| --- | --- | --- |
| Calibrate on start | Switch, *Configuration* | Calibrates when the detection starts. |
| Automatic recalibration | Switch, *Configuration* | Lets the Board Manager recalibrate by itself. |
| Automatic distortion correction | Switch, *Configuration* | Corrects lens distortion during calibration. |
| Camera standby (minutes) | Select, *Configuration* | Puts the cameras on standby after 5, 10, 15, 30 or 60 idle minutes. |

A change is written to the Board Manager configuration; only the changed setting is sent.

## Health and connections

| Entity | Type | Description |
| --- | --- | --- |
| Board Manager connection | Binary sensor, *Diagnostic* | Home Assistant reaches the Board Manager. |
| Realtime connection | Binary sensor, *Diagnostic* | Realtime events arrive. Without them, the integration reads every 2 seconds. |
| Autodarts cloud connection | Binary sensor, **BM 2**, *Diagnostic* | The board's connection to Autodarts. |
| Cameras active | Binary sensor | The cameras are running. |
| Calibration in progress | Binary sensor | A calibration is running. |
| Camera problem | Binary sensor, *Diagnostic* | On when any camera delivers no frames for 15 seconds during active detection. Normal stops, calibration and standby are ignored. |
| Camera *N* problem | Binary sensor, *Diagnostic* | The same for one camera. |
| Detection frame rate | Sensor, fps, *Diagnostic*, *Disabled* | Frames per second of the detection. |
| Camera *N* frame rate | Sensor, fps, *Diagnostic*, *Disabled* | Frames per second of one camera. |
| CPU usage | Sensor, %, **BM 2**, *Diagnostic* | CPU load of the board PC. |
| Memory usage | Sensor, **BM 2**, *Diagnostic*, *Disabled* | Memory use as reported by Board Manager 2. |
| Board software | Update, **BM 2** | Installed and latest Board Manager version. Install updates on the board PC. |

Per-camera entities carry a `camera` attribute with the camera number, which the [status card](cards.md#board-status-card) uses.

## Motion

| Entity | Type | Description |
| --- | --- | --- |
| Hand detected | Binary sensor | A hand is in front of the board. |
| Image stable | Binary sensor | The camera image is steady. |
| Darts partially removed | Binary sensor | Some darts are removed. |
| Darts fully removed | Binary sensor | All darts are removed. |

These sensors are *off* while the detection is stopped, starting, stopping or calibrating.

## Cameras

| Entity | Type | Description |
| --- | --- | --- |
| Camera *N* | Camera, *Disabled* | A snapshot of one board camera, for example in a picture card. The Board Manager offers no video stream. |

## Cloud match data (optional)

These entities exist only with a [linked Autodarts account](installation.md#link-the-autodarts-cloud-optional) and are read every 5 seconds during a match, otherwise once a minute.

| Entity | Type | Description |
| --- | --- | --- |
| Board status | Sensor (enum), *Diagnostic* | `connected` or `disconnected` in the Autodarts cloud. |
| Game mode | Sensor | Variant of the current match, such as `X01` or `Cricket`. |
| Match state | Sensor (enum) | `no_match`, `active` or `finished`. |
| Round | Sensor | Current round. |
| Visit score | Sensor, points | Score of the current visit in the match. |
| Darts thrown | Sensor, darts | Darts thrown in the match. |

Without a local board, *Last board event*, *Last dart* and *Darts in visit* come from the cloud as well.

## Availability

- Local entities become *unavailable* when the Board Manager does not answer and recover on their own.
- Training entities stay available, because the session is stored in Home Assistant.
- If the configured address answers as a **different board**, the entities stay unavailable and Home Assistant shows a repair notice.
- When the board is updated from Board Manager 1 to 2, the integration reloads by itself and adds or removes the generation-specific entities.
