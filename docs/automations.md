# Automations

[← Documentation](README.md) · [Deutsch](de/automationen.md)

Your board is fast enough for automations that happen *while* you play. The light flashes the moment a 180 is complete, and the speaker calls the score before you reach the board.

## Blueprints

Blueprints are ready-made automations. Import one, choose your board and the devices to use, and you're done. They require Home Assistant 2026.8 or newer.

| Blueprint | What it does | Import |
| --- | --- | --- |
| **Celebrate a visit score** | Runs your actions for visits from a minimum score (default 180). The actions can use `score`, `darts` and `segments`. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FDennis-Otto%2Fha-autodarts%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fautodarts%2Fvisit_score.yaml) |
| **Dart caller** | Announces every visit on your speakers with any text-to-speech engine. It has a special message for 180 and can also call every dart. The messages are templates. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FDennis-Otto%2Fha-autodarts%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fautodarts%2Fdart_caller.yaml) |
| **Takeout actions** | Runs actions when you start pulling darts and when the board is clear, for example to brighten the board light. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FDennis-Otto%2Fha-autodarts%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fautodarts%2Ftakeout.yaml) |
| **Start and stop detection automatically** | Starts the detection when someone is at the board and stops it after an idle time you choose, so the cameras and board PC can rest. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FDennis-Otto%2Fha-autodarts%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fautodarts%2Fauto_detection.yaml) |
| **Board problem alert** | Alerts you after a grace period when the board goes offline or a camera fails. An optional all-clear is sent only after a real alert. The actions can use `problem` and `recovered`. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FDennis-Otto%2Fha-autodarts%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fautodarts%2Fboard_alert.yaml) |
| **Training report** | Sends a daily summary of darts, 3-dart average, highest visit and 180s, skipping days without darts. The `summary` variable has the sentence ready. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FDennis-Otto%2Fha-autodarts%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fautodarts%2Ftraining_report.yaml) |
| **Training session routine** | When a [training session](entities.md#training-session) starts, runs your actions, turns on the detection and calibrates the cameras after a short wait; when it ends, turns off the detection and runs your actions with `reason`, `darts`, `average` and `duration_minutes`. The detection switch and the calibration button are optional. | [![Import](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FDennis-Otto%2Fha-autodarts%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fautodarts%2Ftraining_session.yaml) |

Without My Home Assistant, go to **Settings → Automations & scenes → Blueprints → Import blueprint** and paste the link to the file in [`blueprints/automation/autodarts`](../blueprints/automation/autodarts).

### Dart caller messages

The messages of the dart caller are templates. For example:

| Field | Example |
| --- | --- |
| Visit message | `{{ score }}`, or `{{ score }} points` |
| Message for 180 | `One hundred and eighty!` |
| Dart message | `{{ segment \| replace('T', 'Treble ') \| replace('D', 'Double ') \| replace('S', '') }}` |

For a German caller, choose a German text-to-speech voice and enter, for example, `{{ score }} Punkte` and `Einhundertachtzig!`.

## Board events

All realtime moments arrive through the **Board events** entity. Each event carries an `event_type` and its details; see the [event reference](entities.md#board-events).

In the automation editor, choose the trigger **Event received** (*Entity → Event*), select the board events entity and the event types you want. In YAML:

```yaml
triggers:
  - trigger: event.received
    target:
      entity_id: event.autodarts_board_board_events
    options:
      event_type:
        - visit_completed
```

Read the details from `trigger.to_state.attributes`, not from the current state of the entity. Two events can follow each other within milliseconds, for example `visit_completed` and `takeout_finished`, and the current state may already show the second one.

## Examples

### Flash the lights for a 180

```yaml
alias: Darts - 180 light show
triggers:
  - trigger: event.received
    target:
      entity_id: event.autodarts_board_board_events
    options:
      event_type:
        - visit_completed
conditions:
  - condition: template
    value_template: "{{ trigger.to_state.attributes.get('score') == 180 }}"
actions:
  - action: light.turn_on
    target:
      entity_id: light.dartroom
    data:
      effect: colorloop
  - delay: 10
  - action: light.turn_on
    target:
      entity_id: light.dartroom
    data:
      effect: none
      brightness_pct: 100
mode: single
```

### Light up the board while you pull the darts

```yaml
alias: Darts - takeout light
triggers:
  - trigger: event.received
    id: started
    target:
      entity_id: event.autodarts_board_board_events
    options:
      event_type:
        - takeout_started
  - trigger: event.received
    id: finished
    target:
      entity_id: event.autodarts_board_board_events
    options:
      event_type:
        - takeout_finished
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: started
        sequence:
          - action: light.turn_on
            target:
              entity_id: light.board_light
            data:
              brightness_pct: 100
    default:
      - action: light.turn_on
        target:
          entity_id: light.board_light
        data:
          brightness_pct: 60
mode: queued
```

### Notify a camera problem

```yaml
alias: Darts - camera problem
triggers:
  - trigger: state
    entity_id: binary_sensor.autodarts_board_camera_problem
    from: "off"
    to: "on"
    for:
      minutes: 2
actions:
  - action: notify.mobile_app_phone
    data:
      title: Autodarts
      message: A board camera delivers no images. Check the camera and its cable.
mode: single
```

### Stop the detection at night

```yaml
alias: Darts - stop detection at night
triggers:
  - trigger: time
    at: "01:00:00"
conditions:
  - condition: state
    entity_id: switch.autodarts_board_detection
    state: "on"
actions:
  - action: switch.turn_off
    target:
      entity_id: switch.autodarts_board_detection
mode: single
```

### Prepare the board when a training session starts

Switch on the board light, start the detection and calibrate the cameras when a session starts, and switch everything off when it ends. Turn off *Start sessions automatically* and start sessions with the *Training session* switch, for example from the training card.

```yaml
alias: Darts - training session routine
triggers:
  - trigger: event.received
    target:
      entity_id: event.autodarts_board_board_events
    options:
      event_type:
        - session_started
    id: started
  - trigger: event.received
    target:
      entity_id: event.autodarts_board_board_events
    options:
      event_type:
        - session_ended
    id: ended
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: started
        sequence:
          - action: light.turn_on
            target:
              entity_id: light.dart_board
          - action: switch.turn_on
            target:
              entity_id: switch.autodarts_board_detection
          - action: button.press
            target:
              entity_id: button.autodarts_board_start_automatic_calibration
      - conditions:
          - condition: trigger
            id: ended
        sequence:
          - action: switch.turn_off
            target:
              entity_id: switch.autodarts_board_detection
          - action: light.turn_off
            target:
              entity_id: light.dart_board
mode: queued
```

### Start a new training session every Monday

```yaml
alias: Darts - weekly training session
triggers:
  - trigger: time
    at: "04:00:00"
conditions:
  - condition: time
    weekday: mon
actions:
  - action: button.press
    target:
      entity_id: button.autodarts_board_new_training_session
mode: single
```

### Call the game shot in a practice game

Announce a won leg and a bust of the [practice game](entities.md#practice-game) on your speakers, with the name of the player.

```yaml
alias: Darts - practice caller
triggers:
  - trigger: event.received
    target:
      entity_id: event.autodarts_board_board_events
    options:
      event_type:
        - leg_won
        - bust
actions:
  - action: tts.speak
    target:
      entity_id: tts.home_assistant_cloud
    data:
      media_player_entity_id: media_player.darts_room
      message: >-
        {% set event = trigger.to_state.attributes %}
        {% set player = event.name or 'Player ' ~ event.player %}
        {% if event.event_type == 'leg_won' %}
          Game shot, and the leg, {{ player }}, in {{ event.darts }} darts.
        {% else %}
          Bust. {{ player }}, you still need {{ event.remaining }}.
        {% endif %}
mode: queued
```

## Adapting automations from older versions

Since version 1.0, the **Detection status** sensor reports translatable states: `stopped`, `throw`, `takeout_in_progress` and so on. Older versions reported the raw text of the Board Manager, such as `Stopped` or `Takeout in progress`. Update automations that compare against the old text:

| Before | Now |
| --- | --- |
| `Stopped` | `stopped` |
| `Starting`, `Stopping` | `starting`, `stopping` |
| `Throw` | `throw` |
| `Takeout`, `Takeout in progress` | `takeout`, `takeout_in_progress` |
| `Calibrating` | `calibrating` |
| `Error` | `error` |

The UI shows these states in your language. The *Last board event* sensor still reports the raw Board Manager text.
