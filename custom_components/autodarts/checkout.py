"""Checkout suggestions for X01, aimed the way darts players aim."""

from __future__ import annotations

from functools import cache
from itertools import product
from typing import NamedTuple


class Bed(NamedTuple):
    name: str
    score: int
    multiplier: int


SINGLES = [Bed(f"S{number}", number, 1) for number in range(1, 21)] + [Bed("25", 25, 1)]
DOUBLES = [Bed(f"D{number}", 2 * number, 2) for number in range(1, 21)] + [
    Bed("BULL", 50, 2)
]
TREBLES = [Bed(f"T{number}", 3 * number, 3) for number in range(1, 21)]
BEDS = [*SINGLES, *DOUBLES, *TREBLES]

# Doubles that halve into further doubles come first, the bull last.
FINISH_ORDER = [
    *("D20", "D16", "D8", "D18", "D12", "D10", "D4", "D14", "D6", "D2"),
    *("D19", "D17", "D15", "D13", "D11", "D9", "D7", "D5", "D3", "D1"),
    "BULL",
]
# Highest possible checkout: two trebles 20 and the bull, or three trebles 20.
HIGHEST = {True: 170, False: 180}


@cache
def _finishes(
    double_out: bool, preferred: tuple[str, ...] = ()
) -> dict[int, list[tuple[int, Bed]]]:
    """Beds that end a leg, by score, with their rank; preferred doubles first."""
    if double_out:
        order = [*preferred, *(name for name in FINISH_ORDER if name not in preferred)]
        ranked = [(order.index(bed.name), bed) for bed in DOUBLES]
    else:
        # Without double out, the biggest target wins: single before double.
        ranked = [(bed.multiplier, bed) for bed in BEDS]
    finishes: dict[int, list[tuple[int, Bed]]] = {}
    for rank, bed in sorted(ranked):
        finishes.setdefault(bed.score, []).append((rank, bed))
    return finishes


@cache
def checkout(
    remaining: int,
    darts: int = 3,
    double_out: bool = True,
    preferred: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """The preferred way to finish, or an empty tuple when none exists.

    Fewer darts come first, then setups without doubles, a double before the
    bull, as few trebles as possible, the preferred finishing bed and the big
    dart first. Preferred doubles, a player's strongest, rank before the rest.
    """
    if not 0 < remaining <= HIGHEST[double_out] or not 0 < darts <= 3:
        return ()
    finishes = _finishes(double_out, preferred)
    for count in range(darts):
        best: tuple[tuple[int, ...], tuple[Bed, ...]] | None = None
        for setup in product(BEDS, repeat=count):
            need = remaining - sum(bed.score for bed in setup)
            for rank, finish in finishes.get(need, ()):
                key = (
                    sum(bed.multiplier == 2 for bed in setup),
                    finish.name == "BULL",
                    sum(bed.multiplier == 3 for bed in setup),
                    rank,
                    *(-bed.score for bed in setup),
                )
                if best is None or key < best[0]:
                    best = key, (*setup, finish)
        if best:
            return tuple(bed.name for bed in best[1])
    return ()
