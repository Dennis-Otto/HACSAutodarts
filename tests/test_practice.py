"""X01 practice games: counting down, busts, checkouts, corrections and matches."""

from hypothesis import given
from hypothesis import strategies as st

from custom_components.autodarts.checkout import checkout
from custom_components.autodarts.practice import GAMES, MAX_PLAYERS, PracticeGame


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
    """Throw a visit dart by dart and pull the darts; return the events.

    Playing alone, the turn stays with the same player; those events are
    left out here and checked on their own.
    """
    events = []
    for count in range(1, len(names) + 1):
        events += game.track([dart(name) for name in names[:count]])
    events += game.finish_visit()
    game.track([])
    if len(game.players) == 1:
        events = [event for event in events if event[0] != "turn_changed"]
    return events


PLAYER_1 = {"game": 301, "player": 1, "name": None, "players": 1}


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
    assert events == [("bust", {**PLAYER_1, "remaining": 32})]
    assert game.snapshot()["remaining"] == 32
    # One left, or zero without a double, is a bust with double out.
    assert throw(game, "S20", "S11") == [("bust", {**PLAYER_1, "remaining": 32})]
    assert throw(game, "S16", "S16") == [("bust", {**PLAYER_1, "remaining": 32})]
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
        (
            "leg_won",
            {
                **PLAYER_1,
                "darts": 2,
                "average": 451.5,
                "checkout": 40,
                "legs": 1,
                "sets": 0,
                "match": False,
            },
        )
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
    assert game.snapshot() == {
        "game": None,
        "double_out": True,
        "players": 1,
        "legs_to_win": 1,
        "sets_to_win": 1,
        "legs": [],
        "drill": None,
        "double_in": False,
        "bull_off": None,
    }
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
    # Version 1.2 stored one player at the top level.
    stored = game.stored()
    assert stored["players"] == [
        {
            "remaining": 88,
            "darts": 21,
            "points": 0,
            "legs": 0,
            "sets": 0,
            "match_darts": 0,
            "match_points": 0,
            "first9_points": 0,
            "first9_darts": 0,
            "at_double": 0,
            "marks": [0] * 7,
            "marks_hit": 0,
            "match_marks": 0,
            "opened": False,
        }
    ]
    assert stored["double_out"] is False and stored["names"] == [""] * MAX_PLAYERS
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


def match(players: int, legs: int = 1, sets: int = 1, **names) -> PracticeGame:
    game = PracticeGame()
    game.play(301)
    game.set_players(players)
    game.set_format(legs, sets)
    for index, name in names.items():
        game.set_name(int(index[1:]) - 1, name)
    return game


DENNIS = {"game": 301, "player": 1, "name": "Dennis", "players": 2}
LEA = {"game": 301, "player": 2, "name": "Lea", "players": 2}


def test_players_take_turns_and_a_bust_passes_the_turn():
    game = match(2, p1="Dennis", p2=" Lea ")
    assert throw(game, "T20", "T20", "T20") == [
        ("turn_changed", {**LEA, "remaining": 301, "checkout": None})
    ]
    throw(game, "S20")
    scores = game.snapshot()["scores"]
    assert [(score["name"], score["remaining"]) for score in scores] == [
        ("Dennis", 121),
        ("Lea", 281),
    ]
    assert scores[0]["average"] == 180.0 and scores[1]["average"] == 60.0
    # 121 - 120 leaves one: a bust, and the turn passes anyway.
    assert throw(game, "T20", "T20") == [
        ("bust", {**DENNIS, "remaining": 121}),
        ("turn_changed", {**LEA, "remaining": 281, "checkout": None}),
    ]
    assert game.snapshot()["player"] == 2


def test_legs_make_sets_and_sets_make_the_match():
    game = match(2, legs=2, sets=2)
    for leg, starter in enumerate([1, 2, 1, 2], 1):
        assert game.snapshot()["player"] == starter
        if starter == 2:
            throw(game, "MISS")
        game.players[0].remaining = 40
        events = throw(game, "D20")
        kinds = [kind for kind, _ in events]
        if leg < 4:
            assert kinds == ["leg_won", "turn_changed"]
        else:
            assert kinds == ["leg_won", "match_won"]
    won = dict(events)
    assert won["leg_won"]["legs"] == 0 and won["leg_won"]["sets"] == 2
    assert won["match_won"]["player"] == 1 and won["match_won"]["sets"] == 2
    assert won["leg_won"]["match"] is True
    snapshot = game.snapshot()
    assert snapshot["winner"] == 1 and snapshot["checkout"] is None
    assert [score["sets"] for score in snapshot["scores"]] == [2, 0]
    assert len(game.legs) == 4 and game.legs[0]["player"] == 1
    # The result stays until the next dart, which starts a new match.
    game.track([dart("S20")])
    snapshot = game.snapshot()
    assert snapshot["winner"] is None and snapshot["player"] == 1
    assert [score["remaining"] for score in snapshot["scores"]] == [281, 301]
    assert [score["sets"] for score in snapshot["scores"]] == [0, 0]


def test_a_set_won_resets_the_legs_of_everybody():
    game = match(2, legs=2, sets=3)
    game.players[1].legs = 1
    game.players[0].legs = 1
    game.players[0].remaining = 40
    assert [kind for kind, _ in throw(game, "D20")] == ["leg_won", "turn_changed"]
    assert [(player.legs, player.sets) for player in game.players] == [(0, 1), (0, 0)]


def test_settings_start_a_new_match_and_survive_a_restart():
    game = match(3, legs=3, sets=2, p1="Dennis", p3="Max")
    throw(game, "T20")
    assert game.snapshot()["player"] == 2
    restored = PracticeGame()
    restored.restore(game.stored())
    assert restored.stored() == game.stored()
    assert restored.snapshot()["scores"][0]["remaining"] == 241
    game.set_players(9)
    assert len(game.players) == 1 and game.snapshot()["remaining"] == 301
    game.set_format(legs=0, sets=99)
    assert (game.legs_to_win, game.sets_to_win) == (3, 2)
    game.set_name(7, "nobody")
    game.set_name(0, "A very long name that is cut")
    assert game.names[0] == "A very long name tha"


@given(
    st.integers(1, MAX_PLAYERS),
    st.integers(1, 3),
    st.integers(1, 2),
    st.lists(
        st.lists(
            st.sampled_from(["T20", "T19", "S20", "D20", "D16", "BULL", "MISS"]),
            min_size=1,
            max_size=3,
        ),
        max_size=80,
    ),
)
def test_any_match_keeps_turns_and_scores_consistent(players, legs, sets, visits):
    game = match(players, legs, sets)
    for visit in visits:
        before = game.snapshot()
        won = any(kind == "leg_won" for kind, _ in throw(game, *visit))
        snapshot = game.snapshot()
        assert 1 <= snapshot["player"] <= players
        if players > 1 and before["winner"] is None and not won:
            # Every visit passes the turn, unless it won a leg.
            assert snapshot["player"] == before["player"] % players + 1
        for score in snapshot["scores"]:
            if snapshot["winner"] == score["player"]:
                assert score["remaining"] == 0 and score["sets"] == sets
            else:
                assert 0 < score["remaining"] <= 301
                assert score["legs"] < legs or players == 1
                assert score["sets"] < sets or players == 1


def test_playing_alone_the_next_visit_is_announced_with_its_checkout():
    game = playing(301, 141)
    game.track([dart("T20")])
    assert game.finish_visit() == [
        ("turn_changed", {**PLAYER_1, "remaining": 81, "checkout": "T15 D18"})
    ]
    game.players[0].remaining = 40
    game.track([dart("D20")])
    # A won leg starts the next one.
    assert game.finish_visit() == [
        ("turn_changed", {**PLAYER_1, "remaining": 301, "checkout": None})
    ]
