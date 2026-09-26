"""X01 practice legs: counting down, busts, checkouts and corrections."""

from hypothesis import given
from hypothesis import strategies as st

from custom_components.autodarts.checkout import checkout
from custom_components.autodarts.practice import GAMES, PracticeGame


def dart(name: str) -> dict:
    if name == "BULL":
        return {"number": 25, "multiplier": 2, "name": "Bull"}
    if name == "25":
        return {"number": 25, "multiplier": 1, "name": "25"}
    if name == "MISS":
        return {"number": 0, "multiplier": 0, "name": "M"}
    return {
        "number": int(name[1:]),
        "multiplier": "SDT".index(name[0]) + 1,
        "name": name,
    }


def throw(game: PracticeGame, *names: str) -> list[tuple[str, dict]]:
    """Throw a visit dart by dart and pull the darts; return the events."""
    events = []
    for count in range(1, len(names) + 1):
        events += game.track([dart(name) for name in names[:count]])
    game.finish_visit()
    game.track([])
    return events


def playing(start: int, remaining: int | None = None, **settings) -> PracticeGame:
    game = PracticeGame()
    game.restore({"game": start, "remaining": remaining or start, **settings})
    return game


def test_a_leg_counts_down_and_suggests_the_checkout():
    game = playing(501)
    assert throw(game, "T20", "T20", "T20") == []
    snapshot = game.snapshot()
    assert snapshot["remaining"] == 321 and snapshot["darts"] == 3
    assert snapshot["average"] == 180.0 and snapshot["checkout"] is None
    game.restore({"game": 501, "remaining": 100})
    assert game.snapshot()["checkout"] == "T20 D20"
    game.track([dart("S20")])
    snapshot = game.snapshot()
    assert snapshot["remaining"] == 80 and snapshot["visit"] == ["S20"]
    assert snapshot["checkout"] == " ".join(checkout(80, 2))


def test_a_bust_keeps_the_score_of_the_visit_start():
    game = playing(301, 32)
    events = throw(game, "S20", "S20", "S5")
    assert events == [("bust", {"game": 301, "remaining": 32})]
    assert game.snapshot()["remaining"] == 32
    # One left, or zero without a double, is a bust with double out.
    assert throw(game, "S20", "S11") == [("bust", {"game": 301, "remaining": 32})]
    assert throw(game, "S16", "S16") == [("bust", {"game": 301, "remaining": 32})]
    # Darts after a bust are not part of the visit.
    snapshot = game.snapshot()
    assert snapshot["remaining"] == 32 and snapshot["darts"] == 6
    assert snapshot["checkout"] == "D16"


def test_the_bust_shows_until_the_darts_are_pulled():
    game = playing(301, 32)
    game.track([dart("T20")])
    snapshot = game.snapshot()
    assert snapshot["bust"] and snapshot["remaining"] == 32
    assert snapshot["checkout"] == "D16"


def test_a_double_wins_the_leg_and_the_next_leg_starts():
    game = playing(301, 40)
    events = throw(game, "S20", "D10", "T20")
    assert events == [
        ("leg_won", {"game": 301, "darts": 2, "average": 451.5, "checkout": 40})
    ]
    assert game.snapshot()["remaining"] == 301
    assert game.legs[0]["darts"] == 2 and game.legs[0]["checkout"] == 40
    assert throw(game, "BULL") == []
    assert game.snapshot()["remaining"] == 251


def test_without_double_out_any_bed_finishes():
    game = playing(301, 20, double_out=False)
    game.track([dart("S20")])
    assert game.snapshot()["won"] and game.snapshot()["checkout"] is None
    game.finish_visit()
    assert game.legs[0]["checkout"] == 20


def test_corrections_revise_the_visit():
    game = playing(301, 40)
    assert game.track([dart("D20")])[0][0] == "leg_won"
    assert game.track([dart("S20")]) == []
    assert game.snapshot()["remaining"] == 20
    assert game.track([dart("S20"), dart("D10")])[0][0] == "leg_won"


def test_darts_already_thrown_do_not_count_for_a_new_leg():
    game = PracticeGame()
    assert game.track([dart("T20")]) == []
    assert game.snapshot() == {"game": None, "double_out": True, "legs": []}
    game.play(501)
    game.track([dart("T20"), dart("T19")])
    assert game.snapshot()["remaining"] == 444
    game.new_leg()
    game.track([dart("T20"), dart("T19"), dart("S1")])
    assert game.snapshot()["remaining"] == 500
    game.play(0)
    assert game.snapshot()["game"] is None


def test_restore_keeps_valid_data_only():
    game = PracticeGame()
    game.restore({"game": 501, "remaining": 88, "darts": 21, "double_out": False})
    assert game.stored() == {
        "game": 501,
        "double_out": False,
        "remaining": 88,
        "darts": 21,
        "legs": [],
    }
    game.restore({"game": 401, "remaining": 600, "legs": [{"game": 501, "darts": 0}]})
    assert game.game == 501 and game.snapshot()["remaining"] == 501
    assert game.legs == []
    game.restore("broken")
    assert game.game == 501


@given(
    st.sampled_from(GAMES),
    st.booleans(),
    st.lists(
        st.lists(
            st.sampled_from(
                ["T20", "T19", "S20", "S1", "D16", "D1", "BULL", "25", "MISS"]
            ),
            min_size=1,
            max_size=3,
        ),
        max_size=60,
    ),
)
def test_any_visits_keep_the_leg_consistent(start, double_out, visits):
    game = playing(start, double_out=double_out)
    for visit in visits:
        throw(game, *visit)
        remaining = game.snapshot()["remaining"]
        assert 0 < remaining <= start
        assert not double_out or remaining != 1
    for leg in game.legs:
        # Nobody finishes faster than three perfect visits per 180 points.
        assert leg["darts"] >= -(-start // 60)
        assert leg["average"] == round(start * 3 / leg["darts"], 2)
