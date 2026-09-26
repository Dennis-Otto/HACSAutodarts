"""The automation blueprints, run by Home Assistant's own automation engine."""

import asyncio
import shutil
from datetime import timedelta
from pathlib import Path

import pytest
from homeassistant.components.blueprint import models
from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
    get_scheduled_timer_handles,
)

BLUEPRINTS = Path(__file__).parents[1] / "blueprints" / "automation" / "autodarts"
EVENTS = "event.autodarts_board_events"
SOURCE = "https://github.com/Dennis-Otto/ha-autodarts/blob/main/blueprints/automation/autodarts/"


@pytest.fixture(autouse=True)
async def blueprint_folder(hass, tmp_path):
    """Serve the repository blueprints from a temporary configuration folder."""
    hass.config.config_dir = str(tmp_path)
    shutil.copytree(BLUEPRINTS, tmp_path / "blueprints" / "automation" / "autodarts")
    assert await async_setup_component(hass, "event", {})


async def automate(hass, name: str, inputs: dict) -> None:
    config = {"use_blueprint": {"path": f"autodarts/{name}.yaml", "input": inputs}}
    assert await async_setup_component(hass, "automation", {"automation": [config]})
    await hass.async_block_till_done()
    automation = hass.states.async_all("automation")
    assert [state.state for state in automation] == ["on"], automation


def fire(hass, event_type: str, **attributes) -> None:
    hass.states.async_set(
        EVENTS,
        dt_util.utcnow().isoformat(timespec="microseconds"),
        {"event_type": event_type, **attributes},
    )


async def until_waiting(hass, seconds: float) -> None:
    """Let a running automation reach a delay of the given length.

    async_block_till_done() would wait for the whole run, which never ends
    while the clock is frozen.
    """
    for _ in range(200):
        due = [
            handle.when() - hass.loop.time()
            for handle in get_scheduled_timer_handles(hass.loop)
        ]
        if any(seconds - 0.5 < left <= seconds for left in due):
            return
        await asyncio.sleep(0)
    raise AssertionError(f"no delay of {seconds} s started")


@pytest.mark.parametrize(
    "path", sorted(BLUEPRINTS.glob("*.yaml")), ids=lambda p: p.stem
)
def test_blueprint_metadata(path):
    blueprint = models.Blueprint(
        load_yaml(path), expected_domain="automation", schema=BLUEPRINT_SCHEMA
    )
    metadata = blueprint.metadata
    assert metadata["name"].startswith("Autodarts: ")
    assert metadata["source_url"] == SOURCE + path.name
    assert metadata["homeassistant"]["min_version"] == "2026.8.0"
    assert metadata["author"] == "Dennis Otto"


async def test_visit_score_runs_actions_for_high_visits(hass):
    calls = async_mock_service(hass, "test", "celebrate")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "visit_score",
        {
            "board_events": EVENTS,
            "minimum_score": 100,
            "celebration": [
                {
                    "action": "test.celebrate",
                    "data": {"score": "{{ score }}", "segments": "{{ segments }}"},
                }
            ],
        },
    )
    fire(hass, "visit_completed", score=140, darts=3, segments=["T20", "T20", "S20"])
    await hass.async_block_till_done()
    fire(hass, "visit_completed", score=60, darts=3, segments=["S20", "S20", "S20"])
    await hass.async_block_till_done()
    fire(hass, "dart_detected", score=60, segment="T20")
    await hass.async_block_till_done()
    assert [call.data for call in calls] == [
        {"score": 140, "segments": ["T20", "T20", "S20"]}
    ]


async def test_dart_caller_announces_visits_and_darts(hass):
    calls = async_mock_service(hass, "tts", "speak")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "dart_caller",
        {
            "board_events": EVENTS,
            "tts_engine": "tts.home_assistant_cloud",
            "speakers": ["media_player.dartroom"],
            "call_each_dart": True,
        },
    )
    fire(hass, "dart_detected", segment="T20", score=60)
    await hass.async_block_till_done()
    fire(hass, "visit_completed", score=180, darts=3, segments=["T20"] * 3)
    await hass.async_block_till_done()
    fire(hass, "visit_completed", score=45, darts=3, segments=["S5", "S20", "S20"])
    await hass.async_block_till_done()
    assert [str(call.data["message"]) for call in calls] == [
        "T20",
        "One hundred and eighty!",
        "45",
    ]
    assert calls[0].data["media_player_entity_id"] == ["media_player.dartroom"]


async def test_dart_caller_skips_darts_by_default(hass):
    calls = async_mock_service(hass, "tts", "speak")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "dart_caller",
        {
            "board_events": EVENTS,
            "tts_engine": "tts.home_assistant_cloud",
            "speakers": ["media_player.dartroom"],
            "visit_message": "{{ score }} points",
        },
    )
    fire(hass, "dart_detected", segment="T20", score=60)
    await hass.async_block_till_done()
    fire(hass, "visit_completed", score=100, darts=3, segments=["T20", "S20", "S20"])
    await hass.async_block_till_done()
    assert [call.data["message"] for call in calls] == ["100 points"]


async def test_takeout_actions(hass):
    started = async_mock_service(hass, "test", "started")
    finished = async_mock_service(hass, "test", "finished")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "takeout",
        {
            "board_events": EVENTS,
            "takeout_started": [{"action": "test.started"}],
            "takeout_finished": [{"action": "test.finished"}],
        },
    )
    fire(hass, "takeout_started")
    await hass.async_block_till_done()
    assert (len(started), len(finished)) == (1, 0)
    fire(hass, "takeout_finished")
    await hass.async_block_till_done()
    assert (len(started), len(finished)) == (1, 1)


async def test_detection_follows_presence(hass):
    turned_on = async_mock_service(hass, "switch", "turn_on")
    turned_off = async_mock_service(hass, "switch", "turn_off")
    hass.states.async_set("binary_sensor.dartroom", "off")
    hass.states.async_set("switch.autodarts_detection", "off")
    await automate(
        hass,
        "auto_detection",
        {
            "presence": "binary_sensor.dartroom",
            "detection": "switch.autodarts_detection",
            "stop_after": {"minutes": 10},
        },
    )
    hass.states.async_set("binary_sensor.dartroom", "on")
    await hass.async_block_till_done()
    assert [call.data["entity_id"] for call in turned_on] == [
        ["switch.autodarts_detection"]
    ]
    hass.states.async_set("switch.autodarts_detection", "on")
    hass.states.async_set("binary_sensor.dartroom", "off")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    assert not turned_off
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=11))
    await hass.async_block_till_done()
    assert [call.data["entity_id"] for call in turned_off] == [
        ["switch.autodarts_detection"]
    ]


async def test_board_alert_waits_for_the_grace_period(hass, freezer):
    alerts = async_mock_service(hass, "test", "alert")
    recoveries = async_mock_service(hass, "test", "recovered")
    hass.states.async_set("binary_sensor.board_connection", "on")
    hass.states.async_set("binary_sensor.camera_problem", "off")
    await automate(
        hass,
        "board_alert",
        {
            "connection": "binary_sensor.board_connection",
            "camera_problem": "binary_sensor.camera_problem",
            "alert_actions": [
                {"action": "test.alert", "data": {"problem": "{{ problem }}"}}
            ],
            "recovery_actions": [
                {
                    "action": "test.recovered",
                    "data": {
                        "problem": "{{ problem }}",
                        "recovered": "{{ recovered }}",
                    },
                }
            ],
        },
    )
    # A short restart neither alerts nor reports a recovery.
    hass.states.async_set("binary_sensor.board_connection", "off")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=30))
    hass.states.async_set("binary_sensor.board_connection", "on")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=3))
    await hass.async_block_till_done()
    assert not alerts and not recoveries

    hass.states.async_set("binary_sensor.camera_problem", "on")
    await hass.async_block_till_done()
    freezer.tick(timedelta(minutes=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert [call.data for call in alerts] == [{"problem": "cameras"}]
    hass.states.async_set("binary_sensor.camera_problem", "off")
    await hass.async_block_till_done()
    assert [call.data for call in recoveries] == [
        {"problem": "cameras", "recovered": True}
    ]


async def test_training_report(hass, freezer):
    reports = async_mock_service(hass, "test", "report")
    await hass.config.async_set_time_zone("Europe/Berlin")
    freezer.move_to("2026-09-26 20:59:00+02:00")
    for key, value in (
        ("darts", "30"),
        ("average", "57.349"),
        ("highest", "140"),
        ("scores_180", "1"),
    ):
        hass.states.async_set(f"sensor.autodarts_training_{key}", value)
    await automate(
        hass,
        "training_report",
        {
            "darts_sensor": "sensor.autodarts_training_darts",
            "average_sensor": "sensor.autodarts_training_average",
            "highest_sensor": "sensor.autodarts_training_highest",
            "maximum_sensor": "sensor.autodarts_training_scores_180",
            "report_actions": [
                {"action": "test.report", "data": {"message": "{{ summary }}"}}
            ],
        },
    )
    freezer.move_to("2026-09-26 21:00:00+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert [call.data["message"] for call in reports] == [
        "30 darts, 3-dart average 57.3, highest visit 140, 1 × 180."
    ]

    # No report without training.
    hass.states.async_set("sensor.autodarts_training_darts", "0")
    freezer.move_to("2026-09-27 21:00:00+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(reports) == 1
    # Turning the automation off cancels the timer for the next day.
    await hass.services.async_call(
        "automation", "turn_off", {"entity_id": "all"}, blocking=True
    )


async def test_training_session_prepares_and_tidies_up_the_board(hass, freezer):
    turn_on = async_mock_service(hass, "switch", "turn_on")
    turn_off = async_mock_service(hass, "switch", "turn_off")
    press = async_mock_service(hass, "button", "press")
    light = async_mock_service(hass, "test", "light")
    report = async_mock_service(hass, "test", "report")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "training_session",
        {
            "board_events": EVENTS,
            "detection": "switch.autodarts_board_detection",
            "calibration": "button.autodarts_board_calibrate",
            "calibration_delay": 5,
            "session_started": [{"action": "test.light"}],
            "session_ended": [
                {
                    "action": "test.report",
                    "data": {
                        "reason": "{{ reason }}",
                        "darts": "{{ darts }}",
                        "average": "{{ average }}",
                        "minutes": "{{ duration_minutes }}",
                    },
                }
            ],
        },
    )
    fire(hass, "session_started", started="2026-09-26T18:00:00+00:00", reason="manual")
    # The cameras get time to open before the calibration.
    await until_waiting(hass, 5)
    assert len(light) == 1
    assert turn_on[0].data["entity_id"] == ["switch.autodarts_board_detection"]
    assert not press
    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert press[0].data["entity_id"] == ["button.autodarts_board_calibrate"]

    fire(
        hass,
        "session_ended",
        reason="idle",
        darts=30,
        average=48.5,
        duration_minutes=20.0,
    )
    await hass.async_block_till_done()
    assert turn_off[0].data["entity_id"] == ["switch.autodarts_board_detection"]
    assert report[0].data == {
        "reason": "idle",
        "darts": 30,
        "average": 48.5,
        "minutes": 20.0,
    }


async def test_training_session_without_board_controls_only_runs_actions(hass):
    turn_on = async_mock_service(hass, "switch", "turn_on")
    press = async_mock_service(hass, "button", "press")
    light = async_mock_service(hass, "test", "light")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "training_session",
        {"board_events": EVENTS, "session_started": [{"action": "test.light"}]},
    )
    fire(hass, "session_started", started="2026-09-26T18:00:00+00:00")
    await hass.async_block_till_done()
    fire(hass, "session_ended", reason="manual", darts=0)
    await hass.async_block_till_done()
    assert len(light) == 1
    assert not turn_on and not press


async def test_training_session_started_by_a_dart_skips_the_calibration(hass):
    turn_on = async_mock_service(hass, "switch", "turn_on")
    press = async_mock_service(hass, "button", "press")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "training_session",
        {
            "board_events": EVENTS,
            "detection": "switch.autodarts_board_detection",
            "calibration": "button.autodarts_board_calibrate",
            "calibration_delay": 0,
        },
    )
    fire(
        hass,
        "session_started",
        started="2026-09-26T18:00:00+00:00",
        reason="first_dart",
    )
    await hass.async_block_till_done()
    assert turn_on[0].data["entity_id"] == ["switch.autodarts_board_detection"]
    # The dart that started the session is still in the board.
    assert not press


async def test_practice_caller_calls_requirements_busts_and_game_shots(hass):
    calls = async_mock_service(hass, "tts", "speak")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "practice_caller",
        {
            "board_events": EVENTS,
            "tts_engine": "tts.home_assistant_cloud",
            "speakers": ["media_player.dartroom"],
        },
    )
    match = {"game": 501, "players": 2}
    events = [
        (
            "turn_changed",
            {
                **match,
                "player": 2,
                "name": "Sam",
                "remaining": 81,
                "checkout": "T15 D18",
            },
        ),
        # No checkout possible and no turn message: silent.
        (
            "turn_changed",
            {**match, "player": 1, "name": None, "remaining": 321, "checkout": None},
        ),
        ("bust", {**match, "player": 1, "name": None, "remaining": 32}),
        ("leg_won", {**match, "player": 2, "name": "Sam", "darts": 15, "match": False}),
        # The deciding leg leaves the call to the match.
        ("leg_won", {**match, "player": 2, "name": "Sam", "darts": 12, "match": True}),
        ("match_won", {**match, "player": 2, "name": "Sam", "sets": 1}),
        (
            "turn_changed",
            {
                "game": 501,
                "players": 1,
                "player": 1,
                "name": None,
                "remaining": 40,
                "checkout": "D20",
            },
        ),
        (
            "leg_won",
            {"game": 501, "players": 1, "player": 1, "name": None, "match": False},
        ),
        # Cricket has no checkout: the next player stays silent.
        (
            "turn_changed",
            {
                "game": "cricket",
                "players": 2,
                "player": 2,
                "name": "Sam",
                "remaining": None,
                "checkout": None,
                "points": 40,
            },
        ),
        (
            "leg_won",
            {"game": "cricket", "players": 2, "player": 2, "name": "Sam"},
        ),
    ]
    for kind, attributes in events:
        fire(hass, kind, **attributes)
        await hass.async_block_till_done()
    assert [str(call.data["message"]) for call in calls] == [
        "Sam, you require 81",
        "No score",
        "Game shot, and the leg, Sam!",
        "Game shot, and the match, Sam!",
        "You require 40",
        "Game shot, and the leg!",
        "Game shot, and the leg, Sam!",
    ]


async def test_practice_caller_names_unnamed_players_in_its_language(hass):
    calls = async_mock_service(hass, "tts", "speak")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "practice_caller",
        {
            "board_events": EVENTS,
            "tts_engine": "tts.home_assistant_cloud",
            "speakers": ["media_player.dartroom"],
            "turn_message": "{{ who }} ist dran",
            "player_label": "Spieler",
        },
    )
    fire(
        hass,
        "turn_changed",
        game=501,
        players=3,
        player=3,
        name=None,
        remaining=501,
        checkout=None,
    )
    await hass.async_block_till_done()
    assert [str(call.data["message"]) for call in calls] == ["Spieler 3 ist dran"]


async def test_highlight_photo_for_a_180_and_a_checkout(hass):
    photos = async_mock_service(hass, "test", "photo")
    score = "sensor.autodarts_board_detected_visit_score"
    hass.states.async_set(score, "0")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "highlight_photo",
        {
            "visit_score": score,
            "board_events": EVENTS,
            "camera": "camera.autodarts_board_camera_1",
            "photo_actions": [
                {
                    "action": "test.photo",
                    "data": {"image": "{{ image }}", "message": "{{ message }}"},
                }
            ],
        },
    )
    for value in ("60", "120", "180"):
        hass.states.async_set(score, value)
        await hass.async_block_till_done()
    assert [call.data for call in photos] == [
        {
            "image": "/api/camera_proxy/camera.autodarts_board_camera_1",
            "message": "180!",
        }
    ]
    hass.states.async_set(score, "0")
    fire(hass, "leg_won", game=501, players=2, player=2, name="Sam", checkout=121)
    await hass.async_block_till_done()
    assert photos[-1].data["message"] == "Checkout 121 by Sam!"
    # A Cricket leg has no checkout to show.
    fire(hass, "leg_won", game="cricket", players=2, player=1, name="Lea", mpr=2.4)
    await hass.async_block_till_done()
    assert len(photos) == 2


async def test_highlight_photo_can_skip_checkouts_and_lower_the_score(hass):
    photos = async_mock_service(hass, "test", "photo")
    score = "sensor.autodarts_board_detected_visit_score"
    hass.states.async_set(score, "0")
    hass.states.async_set(EVENTS, "unknown")
    await automate(
        hass,
        "highlight_photo",
        {
            "visit_score": score,
            "board_events": EVENTS,
            "camera": "camera.autodarts_board_camera_1",
            "minimum_score": 140,
            "checkouts": False,
            "photo_actions": [
                {"action": "test.photo", "data": {"message": "{{ message }}"}}
            ],
        },
    )
    hass.states.async_set(score, "140")
    await hass.async_block_till_done()
    fire(hass, "leg_won", game=501, players=1, player=1, name=None, checkout=40)
    await hass.async_block_till_done()
    assert [call.data["message"] for call in photos] == ["140!"]
