"""Practice games on the local board: X01 for up to four players, and drills."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from homeassistant.util import dt as dt_util

from .checkout import checkout
from .drills import DRILLS, Drill, make_drill
from .scoring import average as _average
from .scoring import evaluate_visit, finishable, rate, score
from .training import hit_key

GAMES = (301, 501, 701)
LEG_HISTORY = 10
# The statistics cover the last ten legs.
STATS_LEGS = 10
STATS_KEYS = ("first9_points", "first9_darts", "at_double", "checkouts")
MAX_PLAYERS = 4
MAX_LEGS = 11
MAX_SETS = 7
NAME_LENGTH = 20


def _count(value: object, low: int, high: int, default: int) -> int:
    return value if type(value) is int and low <= value <= high else default


@dataclass
class Player:
    """Scores of one player; remaining, darts and points restart every leg."""

    remaining: int = 0
    darts: int = 0
    points: int = 0
    legs: int = 0
    sets: int = 0
    match_darts: int = 0
    match_points: int = 0
    # Points of the first nine darts and darts thrown at a double, per leg.
    first9_points: int = 0
    first9_darts: int = 0
    at_double: int = 0

    def new_leg(self, game: int) -> None:
        self.remaining, self.darts, self.points = game, 0, 0
        self.first9_points, self.first9_darts, self.at_double = 0, 0, 0

    @classmethod
    def restored(cls, saved: object, game: int) -> Player:
        data = saved if isinstance(saved, dict) else {}
        player = cls(
            **{key: _count(data.get(key), 0, 10**6, 0) for key in asdict(cls())}
        )
        if player.remaining > game:
            player.new_leg(game)
        return player


class PracticeGame:
    """X01 legs played with the darts the board detects.

    The training session reports the darts of the current visit; a visit
    ends when the darts are pulled, and then the next player throws. A bust
    keeps the score of the visit start. With several players, legs make sets
    and sets make the match; the result stays until the next dart.
    """

    def __init__(self) -> None:
        # The start score; 0 while no game is played.
        self.game = 0
        self.double_out = True
        self.legs_to_win = 1
        self.sets_to_win = 1
        self.names = [""] * MAX_PLAYERS
        self.players = [Player()]
        self.current = 0
        self.starter = 0
        self.winner: int | None = None
        self.legs: list[dict[str, Any]] = []
        self.leg_stats: list[dict[str, int]] = []
        self.legs_total = 0
        # The training game played instead of X01, if any.
        self.drill: str | None = None
        self.drills: dict[str, Drill] = {kind: make_drill(kind) for kind in DRILLS}
        self._visit: list[dict[str, Any]] = []
        # Darts of the current visit thrown before the leg began.
        self._skip = 0
        self._announced: str | None = None

    # -- storage ---------------------------------------------------------------

    def restore(self, saved: object) -> None:
        if not isinstance(saved, dict):
            return
        if saved.get("game") in GAMES:
            self.game = saved["game"]
        if isinstance(saved.get("double_out"), bool):
            self.double_out = saved["double_out"]
        self.legs_to_win = _count(saved.get("legs_to_win"), 1, MAX_LEGS, 1)
        self.sets_to_win = _count(saved.get("sets_to_win"), 1, MAX_SETS, 1)
        names = saved.get("names")
        if isinstance(names, list):
            self.names = [
                name.strip()[:NAME_LENGTH] if isinstance(name, str) else ""
                for name in [*names, *[""] * MAX_PLAYERS][:MAX_PLAYERS]
            ]
        players = saved.get("players")
        if isinstance(players, list) and 0 < len(players) <= MAX_PLAYERS:
            self.players = [Player.restored(player, self.game) for player in players]
        else:
            # Version 1.2 stored a single player at the top level.
            self.players = [
                Player.restored(
                    {"remaining": saved.get("remaining"), "darts": saved.get("darts")},
                    self.game,
                )
            ]
        last = len(self.players) - 1
        self.current = _count(saved.get("current"), 0, last, 0)
        self.starter = _count(saved.get("starter"), 0, last, 0)
        winner = saved.get("winner")
        self.winner = winner if type(winner) is int and 0 <= winner <= last else None
        for index, player in enumerate(self.players):
            # Only the winner of a finished match has nothing left to score.
            if self.game and not player.remaining and index != self.winner:
                player.new_leg(self.game)
        stats = saved.get("leg_stats")
        self.leg_stats = [
            {key: record[key] for key in STATS_KEYS}
            for record in (stats if isinstance(stats, list) else [])
            if isinstance(record, dict)
            and all(
                type(record.get(key)) is int and record[key] >= 0 for key in STATS_KEYS
            )
        ][:STATS_LEGS]
        total = saved.get("legs_total")
        self.legs_total = total if type(total) is int and total >= 0 else 0
        drills = saved.get("drills")
        for kind, drill in self.drills.items():
            state = drills.get(kind) if isinstance(drills, dict) else None
            if isinstance(state, dict):
                drill.restore(state)
        self.drill = saved["drill"] if saved.get("drill") in DRILLS else None
        if self.drill:
            self.game = 0
        legs = saved.get("legs")
        self.legs = [
            dict(leg)
            for leg in (legs if isinstance(legs, list) else [])
            if isinstance(leg, dict)
            and leg.get("game") in GAMES
            and type(leg.get("darts")) is int
            and leg["darts"] > 0
        ][:LEG_HISTORY]

    def stored(self) -> dict[str, Any]:
        return {
            "game": self.game,
            "double_out": self.double_out,
            "legs_to_win": self.legs_to_win,
            "sets_to_win": self.sets_to_win,
            "names": list(self.names),
            "players": [asdict(player) for player in self.players],
            "current": self.current,
            "starter": self.starter,
            "winner": self.winner,
            "legs": [dict(leg) for leg in self.legs],
            "leg_stats": [dict(record) for record in self.leg_stats],
            "legs_total": self.legs_total,
            "drill": self.drill,
            "drills": {kind: drill.stored() for kind, drill in self.drills.items()},
        }

    # -- settings --------------------------------------------------------------

    def play(self, game: int | str) -> None:
        """Start an X01 match or a training game, or stop playing with 0."""
        self.drill = game if isinstance(game, str) and game in DRILLS else None
        self.game = game if not self.drill and game in GAMES else 0
        self.new_match()

    def set_players(self, count: int) -> None:
        self.players = [Player() for _ in range(_count(count, 1, MAX_PLAYERS, 1))]
        self.new_match()

    def set_format(self, legs: int | None = None, sets: int | None = None) -> None:
        if legs is not None:
            self.legs_to_win = _count(legs, 1, MAX_LEGS, self.legs_to_win)
        if sets is not None:
            self.sets_to_win = _count(sets, 1, MAX_SETS, self.sets_to_win)
        self.new_match()

    def set_name(self, index: int, name: str) -> None:
        if 0 <= index < MAX_PLAYERS:
            self.names[index] = name.strip()[:NAME_LENGTH]

    def new_match(self) -> None:
        """Everybody starts from zero legs and sets; player 1 throws first."""
        self.players = [Player() for _ in self.players]
        self.starter, self.winner = 0, None
        self.new_leg()

    def new_leg(self) -> None:
        """Start the leg from the full score; darts already thrown do not count."""
        if self.drill:
            self.drills[self.drill].reset(len(self._visit))
        for player in self.players:
            player.new_leg(self.game)
        self.current = self.starter
        self._skip = len(self._visit)
        self._announced = None

    # -- play ------------------------------------------------------------------

    def _name(self, index: int) -> str | None:
        return self.names[index] or None

    def _who(self, index: int) -> dict[str, Any]:
        return {
            "game": self.game,
            "player": index + 1,
            "name": self._name(index),
            "players": len(self.players),
        }

    def _thrown(self) -> list[dict[str, Any]]:
        return self._visit[self._skip :]

    def _evaluate(self) -> tuple[int, str | None, int]:
        """Remaining score, outcome and counted darts of the current visit."""
        start = self.players[self.current].remaining
        return evaluate_visit(start, self._thrown(), self.double_out)

    def _result(self, index: int) -> tuple[int, int, bool]:
        """Legs, sets and the match decision after the player wins this leg."""
        player = self.players[index]
        legs, sets = player.legs + 1, player.sets
        if len(self.players) == 1:
            return legs, sets, False
        if legs >= self.legs_to_win:
            legs, sets = 0, sets + 1
        return legs, sets, sets >= self.sets_to_win

    def track(self, visit: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
        """Follow the darts of the current visit, announcing a bust or a win."""
        self._visit = list(visit)
        self._skip = min(self._skip, len(self._visit))
        if self.drill:
            return self.drills[self.drill].track(visit)
        if not self.game:
            return []
        if self.winner is not None and self._thrown():
            # The first dart after a finished match starts the next one.
            self.new_match()
            self._skip = 0
        remaining, outcome, darts = self._evaluate()
        if outcome == self._announced:
            return []
        self._announced = outcome
        player = self.players[self.current]
        if outcome == "bust":
            return [
                ("bust", {**self._who(self.current), "remaining": player.remaining})
            ]
        if outcome != "won":
            return []
        leg_darts = player.darts + darts
        legs, sets, match = self._result(self.current)
        events: list[tuple[str, dict[str, Any]]] = [
            (
                "leg_won",
                {
                    **self._who(self.current),
                    "darts": leg_darts,
                    "average": _average(self.game, leg_darts),
                    "checkout": player.remaining,
                    "legs": legs,
                    "sets": sets,
                    "match": match,
                },
            )
        ]
        if match:
            events.append(
                (
                    "match_won",
                    {
                        **self._who(self.current),
                        "sets": sets,
                        "average": _average(
                            player.match_points + player.remaining,
                            player.match_darts + darts,
                        ),
                    },
                )
            )
        return events

    def finish_visit(self) -> list[tuple[str, dict[str, Any]]]:
        """Book the visit whose darts were pulled; then the next player throws."""
        events: list[tuple[str, dict[str, Any]]] = []
        if self.drill:
            events = self.drills[self.drill].finish_visit()
        elif self.game and self.winner is None and self._thrown():
            remaining, outcome, darts = self._evaluate()
            player = self.players[self.current]
            self._count_visit(player, outcome, darts)
            scored = player.remaining - remaining
            player.darts += darts
            player.points += scored
            player.match_darts += darts
            player.match_points += scored
            if outcome == "won":
                self._book_leg()
            else:
                player.remaining = remaining
                self.current = (self.current + 1) % len(self.players)
            if self.winner is None:
                # Also when playing alone: the next visit is up, for callers.
                up = self.players[self.current]
                route = checkout(up.remaining, 3, self.double_out)
                events.append(
                    (
                        "turn_changed",
                        {
                            **self._who(self.current),
                            "remaining": up.remaining,
                            "checkout": " ".join(route) or None,
                        },
                    )
                )
        self._visit, self._skip, self._announced = [], 0, None
        return events

    def _count_visit(self, player: Player, outcome: str | None, darts: int) -> None:
        """First nine darts and darts at a double of the visit being booked."""
        running = player.remaining
        for dart in self._thrown()[:darts]:
            if self.double_out and finishable(running):
                player.at_double += 1
            if player.first9_darts < 9:
                player.first9_darts += 1
                # A bust visit scores nothing, not even its early darts.
                player.first9_points += 0 if outcome == "bust" else score(dart)
            running -= score(dart)

    def _book_stats(self) -> None:
        """One record per leg for everybody at the board, then a fresh count."""
        self.leg_stats.insert(
            0,
            {
                "first9_points": sum(player.first9_points for player in self.players),
                "first9_darts": sum(player.first9_darts for player in self.players),
                "at_double": sum(player.at_double for player in self.players),
                "checkouts": int(self.double_out),
            },
        )
        del self.leg_stats[STATS_LEGS:]
        self.legs_total += 1
        for player in self.players:
            player.first9_points, player.first9_darts, player.at_double = 0, 0, 0

    def statistics(self) -> dict[str, Any]:
        """Averages and rates of the last ten legs and the double drills."""
        totals = {
            key: sum(record[key] for record in self.leg_stats) for key in STATS_KEYS
        }
        drill_darts, drill_hits = 0, 0
        for kind in ("doubles", "bobs_27"):
            for result in self.drills[kind].results:
                darts, hits = result.get("darts"), result.get("hits")
                if type(darts) is int and type(hits) is int and 0 <= hits <= darts:
                    drill_darts += darts
                    drill_hits += hits
        return {
            "first_9_average": _average(
                totals["first9_points"], totals["first9_darts"]
            ),
            "checkout_rate": rate(totals["checkouts"], totals["at_double"]),
            "doubles_rate": rate(
                totals["checkouts"] + drill_hits, totals["at_double"] + drill_darts
            ),
            "legs_played": self.legs_total,
            "legs_counted": len(self.leg_stats),
            "darts_at_double": totals["at_double"] + drill_darts,
        }

    def _book_leg(self) -> None:
        self._book_stats()
        winner = self.players[self.current]
        self.legs.insert(
            0,
            {
                **self._who(self.current),
                "darts": winner.darts,
                "average": _average(self.game, winner.darts),
                "checkout": winner.remaining,
                "ended": dt_util.utcnow().isoformat(),
            },
        )
        del self.legs[LEG_HISTORY:]
        winner.legs, winner.sets, match = self._result(self.current)
        if match:
            winner.remaining = 0
            self.winner = self.current
            return
        if winner.legs == 0:
            # A won set starts the next one from zero legs for everybody.
            for player in self.players:
                player.legs = 0
        self.starter = (self.starter + 1) % len(self.players)
        for player in self.players:
            player.new_leg(self.game)
        self.current = self.starter

    # -- state -----------------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        common = {
            "double_out": self.double_out,
            "players": len(self.players),
            "legs_to_win": self.legs_to_win,
            "sets_to_win": self.sets_to_win,
            "legs": self.legs,
            "drill": self.drills[self.drill].snapshot() if self.drill else None,
        }
        if not self.game:
            return {"game": None, **common}
        remaining, outcome, darts = self._evaluate()
        thrown = len(self._thrown())
        if outcome == "won" or self.winner is not None:
            route: tuple[str, ...] = ()
        elif outcome == "bust" or thrown >= 3:
            # The visit is over; the next one starts with three darts.
            route = checkout(remaining, 3, self.double_out)
        else:
            route = checkout(remaining, 3 - thrown, self.double_out)
        player = self.players[self.current]
        scored = player.remaining - remaining
        leg_darts = player.darts + darts
        return {
            "game": self.game,
            **common,
            "player": self.current + 1,
            "name": self._name(self.current),
            "winner": None if self.winner is None else self.winner + 1,
            "remaining": remaining,
            "checkout": " ".join(route) or None,
            "bust": outcome == "bust",
            "won": outcome == "won",
            "visit": [hit_key(dart) for dart in self._thrown()],
            "darts": leg_darts,
            "average": _average(player.points + scored, leg_darts),
            "scores": [
                {
                    "player": index + 1,
                    "name": self._name(index),
                    "remaining": remaining if index == self.current else item.remaining,
                    "legs": item.legs,
                    "sets": item.sets,
                    "average": _average(
                        item.match_points + (scored if index == self.current else 0),
                        item.match_darts + (darts if index == self.current else 0),
                    ),
                }
                for index, item in enumerate(self.players)
            ],
        }
