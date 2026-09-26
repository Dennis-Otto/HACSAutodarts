"""Checkout routes: the ones players aim for, and never an impossible one."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from custom_components.autodarts.checkout import BEDS, DOUBLES, checkout

BY_NAME = {bed.name: bed for bed in BEDS}


def reachable(darts: int, double_out: bool) -> set[int]:
    """Every score that can be finished with up to this many darts."""
    finishes = {bed.score for bed in (DOUBLES if double_out else BEDS)}
    scores = {bed.score for bed in BEDS}
    result, setups = set(), {0}
    for _ in range(darts):
        result |= {setup + finish for setup in setups for finish in finishes}
        setups = {setup + score for setup in setups for score in scores}
    return result


@pytest.mark.parametrize(
    ("remaining", "route"),
    [
        (170, "T20 T20 BULL"),
        (167, "T20 T19 BULL"),
        (160, "T20 T20 D20"),
        (150, "T20 T18 D18"),
        (120, "T20 S20 D20"),
        (110, "T20 BULL"),
        (100, "T20 D20"),
        (81, "T15 D18"),
        (61, "25 D18"),
        (60, "S20 D20"),
        (50, "BULL"),
        (40, "D20"),
        (32, "D16"),
        (3, "S1 D1"),
        (2, "D1"),
    ],
)
def test_well_known_routes(remaining, route):
    assert " ".join(checkout(remaining)) == route


def test_bogey_numbers_limits_and_darts_left():
    impossible = [score for score in range(1, 200) if not checkout(score)]
    assert impossible == [1, 159, 162, 163, 165, 166, 168, 169, *range(171, 200)]
    assert checkout(0) == checkout(-5) == checkout(50, 0) == ()
    assert checkout(40, 1) == ("D20",)
    assert checkout(41, 1) == checkout(100, 1) == ()
    assert checkout(100, 2) == ("T20", "D20")


def test_single_out_finishes_on_any_bed():
    assert checkout(20, 1, double_out=False) == ("S20",)
    assert checkout(60, 3, double_out=False) == ("T20",)
    assert checkout(180, 3, double_out=False) == ("T20", "T20", "T20")
    assert checkout(181, 3, double_out=False) == ()


@given(st.integers(-5, 190), st.integers(1, 3), st.booleans())
def test_a_route_adds_up_ends_right_and_exists_whenever_possible(
    remaining, darts, double_out
):
    route = checkout(remaining, darts, double_out)
    assert bool(route) == (remaining in reachable(darts, double_out))
    if route:
        beds = [BY_NAME[name] for name in route]
        assert sum(bed.score for bed in beds) == remaining
        assert len(beds) <= darts
        assert not double_out or beds[-1].multiplier == 2
        # No route with fewer darts exists.
        assert remaining not in reachable(len(beds) - 1, double_out)
