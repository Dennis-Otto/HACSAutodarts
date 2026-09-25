"""The automation blueprints, run by Home Assistant's own automation engine."""

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
)

BLUEPRINTS = Path(__file__).parents[1] / "blueprints" / "automation" / "autodarts"
EVENTS = "event.autodarts_board_events"
SOURCE = "https://github.com/Dennis-Otto/HACSAutodarts/blob/main/blueprints/automation/autodarts/"


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
