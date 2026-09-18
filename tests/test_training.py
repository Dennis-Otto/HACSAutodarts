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
        "triples": 3,
        "bulls": 2,
        "scores_180": 1,
        "points": 255,
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


def test_partial_takeout_never_counts_remaining_darts_again():
    session = TrainingSession()
    session.observe(board())
    session.observe(board(T20, S20, BULL))
    session.observe(board(S20, BULL))
    session.observe(board(BULL))
    session.observe(board())
    assert session.snapshot()["darts"] == 3
    assert session.snapshot()["points"] == 130
    session.observe(board(S20))
    assert session.snapshot()["darts"] == 4


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
