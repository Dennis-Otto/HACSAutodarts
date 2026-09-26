"""Party games for one to four players: Shanghai, Halve-It and Killer; and the bull-off.

A party game follows the darts of the visit for the player at the board and
books the visit when the darts are pulled, like X01. It knows its own rules:
who throws next, when a player wins at once, and who wins at the end.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .scoring import BULL, score

PARTY_GAMES = ("shanghai", "halve_it", "killer")
SHANGHAI_ROUNDS = 7
# Halve-It: a number, any double (D), any treble (T) or the bull per round.
HALVE_IT_TARGETS = ("15", "16", "D", "17", "18", "T", "19", "20", "BULL")
HALVE_IT_START = 40
KILLER_LIVES = 3
# Board Manager positions are relative to the outer edge of the double ring.
BOARD_RADIUS_MM = 170
# Without a position, the bed tells how close a dart came to the centre.
BED_DISTANCE_MM = {50: 0.0, 25: 11.0}


def distance_mm(dart: dict[str, Any], position: tuple[float, float] | None) -> float:
    """How far a dart landed from the centre of the board, in millimetres."""
    if position is not None:
        return round(math.hypot(*position) * BOARD_RADIUS_MM, 1)
    return BED_DISTANCE_MM.get(score(dart), float(BOARD_RADIUS_MM))


class BullOff:
    """Every player throws one dart at the bull; the closest starts the match.

    Players whose darts land equally close throw again among themselves.
    """

    def __init__(self, order: list[int]) -> None:
        self.order = list(order)
        self.index = 0
        self.distances: dict[int, float] = {}

    @property
    def thrower(self) -> int:
        return self.order[self.index]

    def book(
        self, dart: dict[str, Any], position: tuple[float, float] | None
    ) -> int | None:
        """The first dart of the visit counts; the winner once everybody threw."""
        self.distances[self.thrower] = distance_mm(dart, position)
        self.index += 1
        if self.index < len(self.order):
            return None
        best = min(self.distances.values())
        closest = [player for player in self.order if self.distances[player] == best]
        if len(closest) == 1:
            return closest[0]
        self.order, self.index, self.distances = closest, 0, {}
        return None

    def stored(self) -> dict[str, Any]:
        return {"order": self.order, "index": self.index, "distances": self.distances}

    @classmethod
    def restored(cls, saved: object, players: int) -> BullOff | None:
        if not isinstance(saved, dict):
            return None
        order = saved.get("order")
        if (
            not isinstance(order, list)
            or not order
            or not all(
                type(player) is int and 0 <= player < players for player in order
            )
            or len(set(order)) != len(order)
        ):
            return None
        bull_off = cls(order)
        index = saved.get("index")
        bull_off.index = index if type(index) is int and 0 <= index < len(order) else 0
        distances = saved.get("distances")
        if isinstance(distances, dict):
            for key, value in distances.items():
                player = int(key) if str(key).isdigit() else -1
                if player in order[: bull_off.index] and isinstance(value, int | float):
                    bull_off.distances[player] = float(value)
        if len(bull_off.distances) != bull_off.index:
            bull_off.index, bull_off.distances = 0, {}
        return bull_off


@dataclass
class Visit:
    """What a visit changes, worked out without booking it."""

    points: list[int]
    won: int | None = None
    lives: list[int] = field(default_factory=list)
    killers: list[bool] = field(default_factory=list)
    numbers: list[int | None] = field(default_factory=list)
    hits: int = 0


class PartyGame(ABC):
    """The rules of one party game for the players at the board."""

    kind = ""
    start = 0

    def __init__(self, players: int) -> None:
        self.players = players
        self.new_leg(players, 0)

    def new_leg(self, players: int, starter: int) -> None:
        self.players = players
        self.starter = starter
        self.points = [self.start] * players
        self.hits = [0] * players
        self.turns = 0

    @property
    def round(self) -> int:
        return self.turns // self.players + 1

    @abstractmethod
    def target(self, player: int) -> str | None:
        """What the player aims at next, if the game names one."""

    @abstractmethod
    def visit(self, player: int, darts: list[dict[str, Any]]) -> Visit:
        """What the darts of the visit change, without booking them."""

    def book(self, player: int, darts: list[dict[str, Any]]) -> Visit:
        """Keep the visit; the winner when it decides the leg."""
        result = self.visit(player, darts)
        self.points = result.points
        self.hits[player] += result.hits
        self.turns += 1
        if result.won is None:
            result.won = self._decided()
        return result

    def _decided(self) -> int | None:
        return None

    def next(self, player: int) -> int:
        return (player + 1) % self.players

    def _best(self) -> int | None:
        """The most points win; more hits break a tie, otherwise nobody wins."""
        ranking = sorted(
            range(self.players),
            key=lambda index: (self.points[index], self.hits[index]),
            reverse=True,
        )
        first = ranking[0]
        if len(ranking) > 1 and (self.points[first], self.hits[first]) == (
            self.points[ranking[1]],
            self.hits[ranking[1]],
        ):
            return -1
        return first

    def details(self, player: int) -> dict[str, Any]:
        return {}

    def stored(self) -> dict[str, Any]:
        return {
            "starter": self.starter,
            "points": list(self.points),
            "hits": list(self.hits),
            "turns": self.turns,
        }

    def restore(self, saved: object) -> None:
        if not isinstance(saved, dict):
            return
        size = self.players

        def counts(key: str, low: int = 0) -> list[int] | None:
            values = saved.get(key)
            if (
                isinstance(values, list)
                and len(values) == size
                and all(type(value) is int and value >= low for value in values)
            ):
                return list(values)
            return None

        starter = saved.get("starter")
        self.starter = starter if type(starter) is int and 0 <= starter < size else 0
        self.points = counts("points") or self.points
        self.hits = counts("hits") or self.hits
        turns = saved.get("turns")
        self.turns = turns if type(turns) is int and turns >= 0 else 0


class Shanghai(PartyGame):
    """Seven rounds at 1 to 7; a single, double and treble in one visit wins."""

    kind = "shanghai"

    def target(self, player: int) -> str | None:
        return str(min(self.round, SHANGHAI_ROUNDS))

    def visit(self, player: int, darts: list[dict[str, Any]]) -> Visit:
        number = min(self.round, SHANGHAI_ROUNDS)
        on_target = [dart for dart in darts if dart["number"] == number]
        points = list(self.points)
        points[player] += sum(score(dart) for dart in on_target)
        shanghai = {dart["multiplier"] for dart in on_target} >= {1, 2, 3}
        return Visit(points, player if shanghai else None, hits=len(on_target))

    def _decided(self) -> int | None:
        return self._best() if self.turns >= SHANGHAI_ROUNDS * self.players else None


class HalveIt(PartyGame):
    """Nine targets from 40 points; a visit without a hit halves the score."""

    kind = "halve_it"
    start = HALVE_IT_START

    def target(self, player: int) -> str | None:
        return HALVE_IT_TARGETS[min(self.round, len(HALVE_IT_TARGETS)) - 1]

    @staticmethod
    def hit(dart: dict[str, Any], target: str) -> bool:
        number, multiplier = dart["number"], dart["multiplier"]
        if number == 0 or multiplier == 0:
            return False
        if target == "D":
            return bool(multiplier == 2)
        if target == "T":
            return bool(multiplier == 3)
        if target == "BULL":
            return bool(number == BULL)
        return bool(number == int(target))

    def visit(self, player: int, darts: list[dict[str, Any]]) -> Visit:
        target = self.target(player) or ""
        hits = [dart for dart in darts if self.hit(dart, target)]
        points = list(self.points)
        points[player] += sum(score(dart) for dart in hits)
        if not hits and len(darts) >= 3:
            points[player] //= 2
        return Visit(points, hits=len(hits))

    def book(self, player: int, darts: list[dict[str, Any]]) -> Visit:
        # A visit ends with fewer than three darts when darts miss the board.
        if not any(self.hit(dart, self.target(player) or "") for dart in darts):
            darts = [*darts, *[{"number": 0, "multiplier": 0}] * 3][:3]
        return super().book(player, darts)

    def _decided(self) -> int | None:
        done = self.turns >= len(HALVE_IT_TARGETS) * self.players
        return self._best() if done else None


class Killer(PartyGame):
    """Everybody picks a number; hit your double to become a killer, then
    take the lives of the others with their doubles. The last one alive wins.
    """

    kind = "killer"

    def new_leg(self, players: int, starter: int) -> None:
        super().new_leg(players, starter)
        self.numbers: list[int | None] = [None] * players
        self.lives = [KILLER_LIVES] * players
        self.killers = [False] * players

    @property
    def choosing(self) -> bool:
        return None in self.numbers

    def target(self, player: int) -> str | None:
        number = self.numbers[player]
        if number is None:
            return None
        return None if self.killers[player] else f"D{number}"

    def visit(self, player: int, darts: list[dict[str, Any]]) -> Visit:
        numbers, lives, killers = (
            list(self.numbers),
            list(self.lives),
            list(self.killers),
        )
        if self.choosing:
            # One dart picks a number that nobody has yet.
            dart = darts[0] if darts else None
            if dart and 1 <= dart["number"] <= 20 and dart["number"] not in numbers:
                numbers[player] = dart["number"]
            return Visit(list(self.points), None, lives, killers, numbers)
        won = None
        for dart in darts:
            if dart["multiplier"] != 2 or dart["number"] not in numbers:
                continue
            owner = numbers.index(dart["number"])
            if owner == player and not killers[player]:
                killers[player] = True
            elif killers[player] and lives[owner] > 0:
                # A killer hitting their own double loses a life, too.
                lives[owner] -= 1
                if lives[player] == 0:
                    killers[player] = False
            alive = [index for index, left in enumerate(lives) if left > 0]
            if len(alive) == 1:
                won = alive[0]
                break
        return Visit(list(self.points), won, lives, killers, numbers)

    def book(self, player: int, darts: list[dict[str, Any]]) -> Visit:
        # Only a dart decides a Killer leg, never the end of a round.
        result = super().book(player, darts)
        self.numbers, self.lives, self.killers = (
            result.numbers,
            result.lives,
            result.killers,
        )
        return result

    def next(self, player: int) -> int:
        if self.choosing and self.numbers[player] is None:
            # A dart that picked no number is thrown again.
            return player
        following = player
        for _ in range(self.players):
            following = (following + 1) % self.players
            if self.choosing:
                if self.numbers[following] is None:
                    return following
            elif self.lives[following] > 0:
                return following
        return player

    def details(self, player: int) -> dict[str, Any]:
        return {
            "number": self.numbers[player],
            "lives": self.lives[player],
            "killer": self.killers[player],
        }

    def stored(self) -> dict[str, Any]:
        return {
            **super().stored(),
            "numbers": list(self.numbers),
            "lives": list(self.lives),
            "killers": list(self.killers),
        }

    def restore(self, saved: object) -> None:
        super().restore(saved)
        if not isinstance(saved, dict):
            return
        numbers, lives, killers = (
            saved.get("numbers"),
            saved.get("lives"),
            saved.get("killers"),
        )
        size = self.players
        if (
            isinstance(numbers, list)
            and len(numbers) == size
            and all(
                number is None or (type(number) is int and 1 <= number <= 20)
                for number in numbers
            )
            and len({number for number in numbers if number is not None})
            == len([number for number in numbers if number is not None])
        ):
            self.numbers = list(numbers)
        if (
            isinstance(lives, list)
            and len(lives) == size
            and all(type(left) is int and 0 <= left <= KILLER_LIVES for left in lives)
        ):
            self.lives = list(lives)
        if isinstance(killers, list) and len(killers) == size:
            self.killers = [killer is True for killer in killers]


GAME_RULES: dict[str, type[PartyGame]] = {
    "shanghai": Shanghai,
    "halve_it": HalveIt,
    "killer": Killer,
}


def make_party(kind: str, players: int) -> PartyGame:
    return GAME_RULES[kind](players)
