"""Party games, X01 variants and the bull-off."""

from hypothesis import given
from hypothesis import strategies as st

from custom_components.autodarts.party import (
    HALVE_IT_START,
    KILLER_LIVES,
    BullOff,
    distance_mm,
    make_party,
)
from custom_components.autodarts.practice import MAX_PLAYERS, PracticeGame

from .test_practice import dart, throw


def game_of(kind: str | int, players: int = 1, **names: str) -> PracticeGame:
    game = PracticeGame()
    game.set_players(players)
    for index, name in names.items():
        game.set_name(int(index[1:]) - 1, name)
    game.play(kind)
    return game


def kinds(events: list) -> list[str]:
    return [kind for kind, _ in events]


def test_x01_starts_from_101_to_1001():
    for start in (101, 901, 1001):
        assert game_of(start).snapshot()["remaining"] == start
    assert game_of(401).snapshot()["game"] is None


def test_double_in_scores_from_the_first_double():
    game = game_of(301)
    game.double_in = True
    game.new_match()
    game.track([dart("S20"), dart("T20")])
    snapshot = game.snapshot()
    assert snapshot["remaining"] == 301 and snapshot["opened"] is False
    assert snapshot["checkout"] is None
    throw(game, "S20", "T20")
    # The single before the double scores nothing; the double and later darts do.
    throw(game, "S1", "D10", "T20")
    player = game.players[0]
    assert player.remaining == 221 and player.opened is True
    assert (player.first9_darts, player.first9_points) == (5, 80)
    assert game.snapshot()["scores"][0]["opened"] is True


def test_a_bust_takes_the_opening_double_back():
    game = game_of(301)
    game.double_in = True
    game.new_match()
    game.players[0].remaining = 50
    assert kinds(throw(game, "D20", "T20")) == ["bust"]
    assert game.players[0].remaining == 50 and game.players[0].opened is False


def test_shanghai_wins_at_once_with_single_double_and_treble():
    game = game_of("shanghai", 2, p1="Alex", p2="Sam")
    assert game.snapshot()["target"] == "1" and game.snapshot()["round"] == 1
    throw(game, "S1", "D1", "S5")
    throw(game, "T1")
    snapshot = game.snapshot()
    assert [score["points"] for score in snapshot["scores"]] == [3, 3]
    assert snapshot["target"] == "2" and snapshot["round"] == 2
    events = throw(game, "S2", "T2", "D2")
    assert kinds(events) == ["leg_won", "match_won"]
    won = dict(events)["leg_won"]
    assert (won["game"], won["name"], won["points"], won["darts"]) == (
        "shanghai",
        "Alex",
        15,
        6,
    )
    assert game.snapshot()["winner"] == 1


def test_shanghai_ends_after_seven_rounds_and_a_tie_replays_the_leg():
    game = game_of("shanghai")
    for number in range(1, 7):
        assert throw(game, f"S{number}") == []
    events = throw(game, "D7")
    assert kinds(events) == ["leg_won"]
    assert dict(events)["leg_won"]["points"] == sum(range(1, 7)) + 14
    # The next leg starts again at the 1.
    assert game.snapshot()["target"] == "1"

    tied = game_of("shanghai", 2)
    for _ in range(7):
        throw(tied, "MISS")
        throw(tied, "MISS")
    assert tied.winner is None and tied.starter == 1
    assert tied.snapshot()["player"] == 2 and tied.snapshot()["round"] == 1


def test_halve_it_halves_a_round_without_a_hit():
    game = game_of("halve_it")
    assert game.snapshot()["points"] == HALVE_IT_START
    throw(game, "S15", "T15", "MISS")
    assert game.snapshot()["points"] == 100 and game.snapshot()["target"] == "16"
    throw(game, "S5", "S5", "S5")
    assert game.snapshot()["points"] == 50 and game.snapshot()["target"] == "D"
    throw(game, "D10")
    assert game.snapshot()["points"] == 70 and game.snapshot()["target"] == "17"
    # Pulling the darts early after a miss halves as well.
    throw(game, "S5")
    assert game.snapshot()["points"] == 35 and game.snapshot()["target"] == "18"
    throw(game, "T18")
    throw(game, "T5")
    throw(game, "S19")
    throw(game, "S20")
    events = throw(game, "25", "BULL")
    assert kinds(events) == ["leg_won"]
    # 35 + 54 + 15 (any treble) + 19 + 20 + 75 (the bull)
    assert dict(events)["leg_won"]["points"] == 218


def test_killer_needs_two_players():
    game = game_of("killer")
    snapshot = game.snapshot()
    assert snapshot["needs_players"] == 2 and snapshot["target"] is None
    assert throw(game, "D20") == [] and game.party.numbers == [None]


def test_killer_picks_numbers_then_the_killers_take_lives():
    game = game_of("killer", 3, p1="Alex", p2="Sam", p3="Kim")
    assert game.snapshot()["phase"] == "choose"
    throw(game, "S7")
    # Sam hits the 7 as well: taken, so Sam throws again.
    throw(game, "S7")
    assert game.snapshot()["player"] == 2
    throw(game, "S12")
    throw(game, "BULL")
    throw(game, "S3")
    snapshot = game.snapshot()
    assert snapshot["phase"] == "play" and snapshot["player"] == 1
    assert [score["number"] for score in snapshot["scores"]] == [7, 12, 3]
    assert snapshot["target"] == "D7"
    # Alex becomes a killer and hunts the others from the next dart on.
    game.track([dart("D7")])
    assert game.snapshot()["target"] is None
    # ... and takes two of Sam's lives.
    throw(game, "D7", "D12", "D12")
    scores = game.snapshot()["scores"]
    assert scores[0]["killer"] is True and scores[1]["lives"] == KILLER_LIVES - 2
    throw(game, "S1")
    throw(game, "D3")
    # A killer hitting their own double loses a life.
    throw(game, "D12", "D7")
    scores = game.snapshot()["scores"]
    assert scores[1]["lives"] == 0 and scores[0]["lives"] == KILLER_LIVES - 1
    # Sam is out: Kim throws next.
    assert game.snapshot()["player"] == 3
    throw(game, "S1")
    events = throw(game, "D3", "D3", "D3")
    assert kinds(events) == ["leg_won", "match_won"]
    assert dict(events)["leg_won"]["name"] == "Alex"


def test_only_killers_take_lives_and_a_killer_can_lose_the_last_one():
    game = game_of("killer", 2, p1="Alex", p2="Sam")
    throw(game, "S7")
    throw(game, "S12")
    # Alex is no killer yet: Sam's double takes no life.
    throw(game, "D12")
    assert game.party.lives == [KILLER_LIVES] * 2
    throw(game, "MISS")
    game.party.killers[0], game.party.lives[0] = True, 1
    # With the last life, Alex hits the own double: Sam is the last one left.
    events = game.track([dart("D7")])
    assert kinds(events) == ["leg_won", "match_won"]
    assert dict(events)["leg_won"]["name"] == "Sam"
    alex = game.snapshot()["scores"][0]
    assert alex["lives"] == 0 and alex["killer"] is False


def test_a_correction_can_take_a_shanghai_back():
    game = game_of("shanghai", 2)
    shanghai = [dart("S1"), dart("D1"), dart("T1")]
    assert kinds(game.track(shanghai)) == ["leg_won", "match_won"]
    # The board corrects the treble to a single: no Shanghai after all.
    assert game.track([dart("S1"), dart("D1"), dart("S1")]) == []
    assert game.snapshot()["winner"] is None
    assert kinds(game.finish_visit()) == ["turn_changed"]
    assert game.snapshot()["player"] == 2 and game.winner is None


def test_killer_turns_skip_players_who_picked_or_are_out():
    killer = make_party("killer", 3)
    killer.restore({"numbers": [7, None, 3]})
    # Whoever still needs a number picks next; a failed pick is thrown again.
    assert killer.next(2) == 1
    assert killer.next(1) == 1
    killer.restore({"numbers": [7, 12, 3], "lives": [0, 2, 0]})
    assert killer.next(1) == 1
    # A stored leg without anybody alive keeps the turn instead of failing.
    killer.restore({"lives": [0, 0, 0]})
    assert killer.next(2) == 2


def test_a_party_game_without_usable_scores_starts_the_leg_fresh():
    game = game_of("killer", 2)
    throw(game, "S5")
    saved = game.stored()
    saved["party"] = "broken"
    restored = PracticeGame()
    restored.restore(saved)
    assert restored.party.kind == "killer"
    assert restored.party.numbers == [None, None]
    assert restored.party.lives == [KILLER_LIVES] * 2


def test_a_restored_bull_off_drops_distances_it_cannot_trust():
    kept = BullOff.restored({"order": [2, 0], "index": 1, "distances": {"2": 5}}, 3)
    assert kept.index == 1 and kept.distances == {2: 5.0} and kept.thrower == 0
    for distances in (
        "broken",
        # Player 3 has not thrown yet and player 2 threw no distance.
        {"0": 11.0, "1": "far", "2": 0.0},
    ):
        restored = BullOff.restored(
            {"order": [0, 1, 2], "index": 2, "distances": distances}, 3
        )
        assert restored.index == 0 and restored.distances == {}
        assert restored.thrower == 0


def test_a_bull_off_decides_who_starts():
    game = PracticeGame()
    game.bull_off = True
    game.set_players(2)
    game.play(501)
    assert game.snapshot()["bull_off"]["player"] == 1
    assert throw(game, "25") == [
        (
            "turn_changed",
            {
                "game": 501,
                "player": 2,
                "name": None,
                "players": 2,
                "remaining": None,
                "checkout": None,
                "bull_off": True,
            },
        )
    ]
    game.track([dart("BULL")])
    assert game.snapshot()["bull_off"]["throws"][1]["distance"] == 0.0
    events = throw(game, "BULL")
    assert events[0] == (
        "bull_off_won",
        {"game": 501, "player": 2, "name": None, "players": 2, "distance": 0.0},
    )
    assert events[1][1]["player"] == 2 and events[1][1]["remaining"] == 501
    snapshot = game.snapshot()
    assert snapshot["bull_off"] is None and snapshot["player"] == 2
    assert [score["remaining"] for score in snapshot["scores"]] == [501, 501]


def test_equal_darts_throw_again_and_positions_measure_the_distance():
    bull_off = BullOff([0, 1, 2])
    assert bull_off.book(dart("BULL"), None) is None
    assert bull_off.book(dart("BULL"), None) is None
    assert bull_off.book(dart("S20"), None) is None
    # Only the two in the bullseye throw again.
    assert bull_off.order == [0, 1] and bull_off.index == 0
    assert bull_off.book(dart("25"), (0.05, 0.0)) is None
    assert bull_off.book(dart("25"), (0.0, -0.03)) == 1
    assert distance_mm(dart("25"), (0.03, 0.04)) == 8.5
    assert distance_mm(dart("S20"), None) == 170


def test_party_games_and_the_bull_off_survive_a_restart():
    game = game_of("killer", 2)
    game.bull_off = True
    game.new_match()
    throw(game, "25")
    restored = PracticeGame()
    restored.restore(game.stored())
    assert restored.stored() == game.stored()
    assert restored.bulling is not None and restored.bulling.distances == {0: 11.0}
    throw(restored, "BULL")
    throw(restored, "S5")
    throw(restored, "S9")
    saved = restored.stored()
    again = PracticeGame()
    again.restore(saved)
    # Player 2 won the bull-off, so player 2 picked first.
    assert again.party.numbers == [9, 5] and again.snapshot()["phase"] == "play"
    saved["party"] = {"numbers": [5, 5], "lives": [9, 1], "killers": "x"}
    saved["bulling"] = {"order": [0, 0]}
    again.restore(saved)
    assert again.party.numbers == [None, None] and again.bulling is None
    assert again.party.lives == [KILLER_LIVES] * 2


BEDS = [
    "S1",
    "D1",
    "T1",
    "S2",
    "D2",
    "T2",
    "S3",
    "D7",
    "D12",
    "S15",
    "T15",
    "BULL",
    "25",
    "MISS",
]


@given(
    st.sampled_from(["shanghai", "halve_it", "killer"]),
    st.integers(1, MAX_PLAYERS),
    st.booleans(),
    st.lists(st.lists(st.sampled_from(BEDS), min_size=1, max_size=3), max_size=60),
)
def test_any_party_game_keeps_its_scores_consistent(kind, players, bull_off, visits):
    game = game_of(kind, players)
    game.bull_off = bull_off
    game.new_match()
    for visit in visits:
        throw(game, *visit)
        snapshot = game.snapshot()
        assert 1 <= snapshot["player"] <= players
        for score in snapshot["scores"]:
            assert score["points"] >= 0
            if kind == "killer":
                assert 0 <= score["lives"] <= KILLER_LIVES
        if (
            kind == "killer"
            and snapshot["phase"] == "play"
            and snapshot["winner"] is None
        ):
            # Nobody who is out ever throws.
            assert snapshot["scores"][snapshot["player"] - 1]["lives"] > 0
