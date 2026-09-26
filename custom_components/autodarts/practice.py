"""An X01 practice leg on the local board: remaining score, busts and checkouts."""

from __future__ import annotations

from typing import Any

from homeassistant.util import dt as dt_util

from .checkout import checkout
from .training import hit_key

GAMES = (301, 501, 701)
LEG_HISTORY = 10


def _score(dart: dict[str, Any]) -> int:
    return int(dart["number"] * dart["multiplier"])


def _double(dart: dict[str, Any]) -> bool:
    """Double rings and the bullseye end a leg with double out."""
    return bool(dart["multiplier"] == 2 and dart["number"] != 0)


def _average(points: int, darts: int) -> float | None:
    return round(points * 3 / darts, 2) if darts else None


class PracticeGame:
    """One X01 leg after another, played with the darts the board detects.

    The training session reports the darts of the current visit; a visit
    ends when the darts are pulled. A bust keeps the score of the visit start.
    """

    def __init__(self) -> None:
        # The start score; 0 while no game is played.
        self.game = 0
        self.double_out = True
        self.legs: list[dict[str, Any]] = []
        self._start = 0
        self._leg_darts = 0
        self._visit: list[dict[str, Any]] = []
        # Darts of the current visit thrown before the leg began.
        self._skip = 0
        self._announced: str | None = None

    def restore(self, saved: object) -> None:
        if not isinstance(saved, dict):
            return
        if saved.get("game") in GAMES:
            self.game = saved["game"]
        if isinstance(saved.get("double_out"), bool):
            self.double_out = saved["double_out"]
        start, darts = saved.get("remaining"), saved.get("darts")
        if self.game and type(start) is int and 0 < start <= self.game:
            self._start = start
            self._leg_darts = darts if type(darts) is int and darts >= 0 else 0
        else:
            self._start, self._leg_darts = self.game, 0
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
            "remaining": self._start,
            "darts": self._leg_darts,
            "legs": [dict(leg) for leg in self.legs],
        }

    def play(self, game: int) -> None:
        """Start a new leg of the game, or stop playing with 0."""
        self.game = game if game in GAMES else 0
        self.new_leg()

    def new_leg(self) -> None:
        """Start from the full score; darts already thrown do not count."""
        self._start = self.game
        self._leg_darts = 0
        self._skip = len(self._visit)
        self._announced = None

    def _thrown(self) -> list[dict[str, Any]]:
        return self._visit[self._skip :]

    def _evaluate(self) -> tuple[int, str | None, int]:
        """Remaining score, outcome and counted darts of the current visit."""
        remaining = self._start
        for index, dart in enumerate(self._thrown(), 1):
            left = remaining - _score(dart)
            if (
                left < 0
                or (self.double_out and left == 1)
                or (left == 0 and self.double_out and not _double(dart))
            ):
                return self._start, "bust", index
            if left == 0:
                return 0, "won", index
            remaining = left
        return remaining, None, len(self._thrown())

    def track(self, visit: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
        """Follow the darts of the current visit, announcing a bust or a win."""
        self._visit = list(visit)
        self._skip = min(self._skip, len(self._visit))
        if not self.game:
            return []
        remaining, outcome, darts = self._evaluate()
        if outcome == self._announced:
            return []
        self._announced = outcome
        if outcome == "bust":
            return [("bust", {"game": self.game, "remaining": self._start})]
        if outcome == "won":
            leg_darts = self._leg_darts + darts
            return [
                (
                    "leg_won",
                    {
                        "game": self.game,
                        "darts": leg_darts,
                        "average": _average(self.game, leg_darts),
                        "checkout": self._start,
                    },
                )
            ]
        return []

    def finish_visit(self) -> None:
        """Book the visit whose darts were pulled."""
        if self.game:
            remaining, outcome, darts = self._evaluate()
            self._leg_darts += darts
            if outcome == "won":
                self.legs.insert(
                    0,
                    {
                        "game": self.game,
                        "darts": self._leg_darts,
                        "average": _average(self.game, self._leg_darts),
                        "checkout": self._start,
                        "ended": dt_util.utcnow().isoformat(),
                    },
                )
                del self.legs[LEG_HISTORY:]
                remaining, self._leg_darts = self.game, 0
            self._start = remaining
        self._visit, self._skip, self._announced = [], 0, None

    def snapshot(self) -> dict[str, Any]:
        if not self.game:
            return {"game": None, "double_out": self.double_out, "legs": self.legs}
        remaining, outcome, darts = self._evaluate()
        thrown = len(self._thrown())
        if outcome == "won":
            route: tuple[str, ...] = ()
        elif outcome == "bust" or thrown >= 3:
            # The visit is over; the next one starts with three darts.
            route = checkout(remaining, 3, self.double_out)
        else:
            route = checkout(remaining, 3 - thrown, self.double_out)
        leg_darts = self._leg_darts + darts
        return {
            "game": self.game,
            "double_out": self.double_out,
            "remaining": remaining,
            "checkout": " ".join(route) or None,
            "bust": outcome == "bust",
            "won": outcome == "won",
            "visit": [hit_key(dart) for dart in self._thrown()],
            "darts": leg_darts,
            "average": _average(self.game - remaining, leg_darts),
            "legs": self.legs,
        }
