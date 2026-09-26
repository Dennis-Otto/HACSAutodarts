"""Cricket rules: marks on 20 to 15 and the bull, points on numbers others need."""

from __future__ import annotations

from typing import Any

# The numbers in the order players close them; 25 is the bull.
CRICKET_NUMBERS = (20, 19, 18, 17, 16, 15, 25)
MARKS_TO_CLOSE = 3


def _marks(dart: dict[str, Any]) -> tuple[int, int]:
    """Slot of the number and marks of one dart; a double counts two."""
    number, multiplier = dart["number"], dart["multiplier"]
    if number not in CRICKET_NUMBERS or multiplier < 1:
        return -1, 0
    return CRICKET_NUMBERS.index(number), multiplier


def marks_per_round(marks: int, darts: int) -> float | None:
    """Marks per three darts, the usual Cricket statistic."""
    return round(marks * 3 / darts, 2) if darts else None


def play_visit(
    marks: list[int],
    points: int,
    darts: list[dict[str, Any]],
    others_marks: list[list[int]],
    others_points: list[int],
) -> tuple[list[int], int, int, bool, int]:
    """Marks, points, counted darts, win and marks that counted after the darts.

    Marks beyond three score the number's value only while another player
    still has it open. Closing everything wins once no one has more points;
    playing alone, closing everything wins.
    """
    marks = list(marks)
    counted = 0
    for count, dart in enumerate(darts, 1):
        slot, add = _marks(dart)
        if add:
            closing = min(MARKS_TO_CLOSE - marks[slot], add)
            marks[slot] += closing
            extra = add - closing
            if extra and any(other[slot] < MARKS_TO_CLOSE for other in others_marks):
                points += extra * CRICKET_NUMBERS[slot]
                counted += add
            else:
                counted += closing
        if all(mark >= MARKS_TO_CLOSE for mark in marks) and all(
            points >= other for other in others_points
        ):
            return marks, points, count, True, counted
    return marks, points, len(darts), False, counted


def next_target(marks: list[int]) -> str | None:
    """The bed to aim at next: the treble of the highest open number, then the bull."""
    for slot, number in enumerate(CRICKET_NUMBERS):
        if marks[slot] < MARKS_TO_CLOSE:
            return "BULL" if number == 25 else f"T{number}"
    return None
