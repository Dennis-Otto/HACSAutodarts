"""A local session must count observations, not messages or camera jitter."""

import pytest

from custom_components.autodarts.training import COUNTERS, TrainingSession


def board(*hits, **changes):
    return {
        "running": True,
        "connected": True,
        "status": "Throw",
        "event": "Throw",
        "numThrows": len(hits),
        "throws": [
            {"segment": {"name": name, "number": number, "multiplier": multiplier}}
            for name, number, multiplier in hits
        ],
        **changes,
    }


T20 = ("T20", 20, 3)
S20 = ("S20", 20, 1)
BULL = ("Bull", 25, 2)
OUTER_BULL = ("25", 25, 1)
MISS = ("M", 0, 0)


def test_visits_duplicates_coordinates_and_bulls():
    session = TrainingSession()
    assert session.observe(board()) == []
    events = []
    for i in range(1, 4):
        events.extend(session.observe(board(*([T20] * i))))
    assert [event[0] for event in events] == ["dart_detected"] * 3
    repeated = board(T20, T20, T20)
    repeated["throws"][0]["coords"] = {"x": 0.1, "y": 0.2}
    assert session.observe(repeated) == []
    assert session.snapshot()["darts"] == 3
    assert session.snapshot()["scores_180"] == 1
    assert session.snapshot()["triples"] == 3
    session.observe(board())
    session.observe(board(BULL, OUTER_BULL, MISS))
    assert {key: session.snapshot()[key] for key in COUNTERS} == {
        "darts": 6,
        "points": 255,
        "doubles": 0,
        "triples": 3,
        "bulls": 2,
        "misses": 1,
        "visits": 2,
        "scores_100": 0,
        "scores_140": 0,
        "scores_180": 1,
    }


def test_corrections_revise_score_and_180_without_adding_darts():
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20, T20, T20))
    events = session.observe(board(T20, S20, T20))
    assert events == [
        ("dart_corrected", {"dart_index": 2, "segment": "S20", "score": 20})
    ]
    assert session.snapshot()["darts"] == 3
    assert session.snapshot()["scores_180"] == 0
    assert session.snapshot()["triples"] == 2
    assert session.snapshot()["points"] == 140
    session.observe(board(T20, T20, T20))
    assert session.snapshot()["scores_180"] == 1
    assert session.snapshot()["points"] == 180


TAKEOUT = {"status": "Takeout in progress", "event": "Takeout started"}


def test_partial_takeout_never_counts_remaining_darts_again():
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20, S20, BULL))
    session.observe(board(S20, BULL, **TAKEOUT))
    session.observe(board(BULL, **TAKEOUT))
    session.observe(board())
    assert session.snapshot()["darts"] == 3
    assert session.snapshot()["points"] == 130
    session.observe(board(S20))
    assert session.snapshot()["darts"] == 4


def test_darts_thrown_before_the_takeout_ends_are_counted():
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20, S20, BULL))
    session.observe(board(BULL, **TAKEOUT))
    events = session.observe(board(BULL, S20))
    assert events == [
        ("dart_detected", {"dart_index": 2, "segment": "S20", "score": 20})
    ]
    assert session.snapshot()["darts"] == 4
    assert session.snapshot()["points"] == 150


def test_missed_empty_board_between_visits_keeps_counting():
    # A slow poll can miss the empty frame; the next visit must still count.
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20, T20, T20))
    events = session.observe(board(S20))
    events += session.observe(board(S20, BULL))
    events += session.observe(board(S20, BULL, OUTER_BULL))
    assert events[0] == (
        "visit_completed",
        {"score": 180, "darts": 3, "segments": ["T20", "T20", "T20"]},
    )
    assert [event[1]["segment"] for event in events[1:]] == ["S20", "Bull", "25"]
    snapshot = session.snapshot()
    assert {key: snapshot[key] for key in ("darts", "bulls", "points")} == {
        "darts": 6,
        "bulls": 2,
        "points": 275,
    }
    assert snapshot["visits"] == 2
    assert snapshot["scores_180"] == 1


def test_transient_shorter_frame_does_not_split_a_visit():
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20, T20))
    assert session.observe(board(T20)) == []
    session.observe(board(T20, T20))
    session.observe(board(T20, T20, T20))
    session.observe(board())
    assert session.snapshot()["darts"] == 3
    assert session.snapshot()["scores_180"] == 1
    assert session.snapshot()["points"] == 180


def test_withdrawn_detection_no_longer_counts():
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20, S20, MISS))
    session.observe(board(T20, S20))
    session.observe(board())
    assert session.snapshot()["darts"] == 2
    assert session.snapshot()["points"] == 80


def test_reset_ignores_darts_already_on_the_board():
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20, T20))
    session.reset(board(T20, T20))
    assert all(session.snapshot()[key] == 0 for key in COUNTERS)
    assert session.observe(board(T20, T20)) == []
    session.observe(board(T20, T20, T20))
    assert session.snapshot()["darts"] == 1
    assert session.snapshot()["scores_180"] == 0
    session.observe(board())
    session.observe(board(T20, T20, T20))
    assert session.snapshot()["darts"] == 4
    assert session.snapshot()["scores_180"] == 1


def test_reload_restores_totals_and_does_not_replay_current_visit():
    old = TrainingSession()
    old.observe(board())
    old.observe(board(T20, T20, T20))
    restored = TrainingSession()
    restored.restore(old.snapshot())
    assert restored.observe(board(T20, T20, T20)) == []
    assert restored.snapshot() == old.snapshot()
    restored.observe(board())
    restored.observe(board(BULL))
    assert restored.snapshot()["darts"] == 4
    assert restored.snapshot()["bulls"] == 1


@pytest.mark.parametrize("status", ["Starting", "Calibrating", "Stopped", "Error"])
def test_inactive_states_do_not_create_training_darts(status):
    session = TrainingSession()
    session.observe(board())
    assert session.observe(board(T20, status=status)) == []
    assert session.snapshot()["darts"] == 0


@pytest.mark.parametrize(
    "invalid",
    [
        {"numThrows": 1, "throws": []},
        {"numThrows": "1"},
        {"numThrows": 1, "throws": [None]},
        {"numThrows": 1, "throws": [{"segment": {"number": "20", "multiplier": 3}}]},
    ],
)
def test_incomplete_or_malformed_snapshot_does_not_reset_visit(invalid):
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20))
    assert session.observe(board(**invalid)) == []
    session.observe(board(T20, S20))
    assert session.snapshot()["darts"] == 2


def test_malformed_storage_is_sanitized():
    session = TrainingSession()
    session.restore({"darts": "bad", "points": -3, "bulls": True, "started": "bad"})
    assert all(session.snapshot()[key] == 0 for key in COUNTERS)


D16 = ("D16", 16, 2)
S1 = ("S1", 1, 1)


def test_analytics_buckets_hits_and_highest_visit():
    session = TrainingSession()
    session.observe(board())
    for visit in ((T20, T20, S20), (T20, S20, S20), (D16, S1, MISS), (T20, T20, T20)):
        for count in range(1, len(visit) + 1):
            session.observe(board(*visit[:count]))
        session.observe(board())
    snapshot = session.snapshot()
    assert snapshot["visits"] == 4
    assert snapshot["scores_100"] == 1  # 100
    assert snapshot["scores_140"] == 1  # 140
    assert snapshot["scores_180"] == 1
    assert snapshot["highest_visit"] == 180
    assert snapshot["doubles"] == 1
    assert snapshot["misses"] == 1
    assert snapshot["hits"] == {"D16": 1, "MISS": 1, "S1": 1, "S20": 3, "T20": 6}


def test_completed_visits_are_announced_once():
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20))
    session.observe(board(T20, S20))
    assert session.observe(board(T20, **TAKEOUT)) == [
        ("visit_completed", {"score": 80, "darts": 2, "segments": ["T20", "S20"]})
    ]
    assert session.observe(board()) == []
    session.observe(board(BULL))
    # Stopping the detection also ends the visit.
    assert session.observe(board(BULL, status="Stopped", running=False)) == [
        ("visit_completed", {"score": 50, "darts": 1, "segments": ["Bull"]})
    ]


def test_average_inputs_and_restore_of_analytics():
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20, D16))
    session.observe(board())
    restored = TrainingSession()
    restored.restore(session.snapshot())
    assert restored.snapshot() == session.snapshot()
    restored.restore(
        {**session.snapshot(), "highest_visit": -1, "hits": {"T20": "x", "S1": 2}}
    )
    assert restored.snapshot()["highest_visit"] == 0
    assert restored.snapshot()["hits"] == {"S1": 2}
    restored.restore({"darts": 3})
    assert restored.snapshot()["hits"] == {}
    restored.reset(board())
    assert restored.snapshot()["highest_visit"] == 0
    assert restored.snapshot()["hits"] == {}
