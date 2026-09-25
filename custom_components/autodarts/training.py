"""Count observed local darts, including corrections, without replaying snapshots."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

# Totals that only grow during a session.
COUNTERS = (
    "darts",
    "points",
    "doubles",
    "triples",
    "bulls",
    "misses",
    "visits",
    "scores_100",
    "scores_140",
    "scores_180",
)
# Visit scores are bucketed like darts statistics: 100-139, 140-179 and 180.
SCORE_BUCKETS = (("scores_100", 100, 140), ("scores_140", 140, 180))


def segments(state: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Use semantic segment values, ignoring jittering camera coordinates."""
    count = state.get("numThrows")
    throws = state.get("throws", [])
    if (
        type(count) is not int
        or count < 0
        or not isinstance(throws, list)
        or len(throws) != count
    ):
        return None
    result = []
    for dart in throws:
        if not isinstance(dart, dict):
            return None
        segment = dart.get("segment") or {}
        if not isinstance(segment, dict):
            return None
        number, multiplier = segment.get("number", 0), segment.get("multiplier", 0)
        if type(number) is not int or type(multiplier) is not int:
            return None
        if number not in (*range(21), 25) or multiplier not in range(4):
            return None
        name = segment.get("name")
        result.append(
            {
                "number": number,
                "multiplier": multiplier,
                "name": name if isinstance(name, str) else None,
            }
        )
    return result


def hit_key(dart: dict[str, Any]) -> str:
    """A stable name per bed: S20, D16, T19, 25 (outer bull), BULL or MISS."""
    number, multiplier = dart["number"], dart["multiplier"]
    if number == 0 or multiplier == 0:
        return "MISS"
    if number == 25:
        return "BULL" if multiplier >= 2 else "25"
    return f"{'SDT'[multiplier - 1]}{number}"


def _visit_summary(darts: list[dict[str, Any]]) -> dict[str, int]:
    points = sum(d["number"] * d["multiplier"] for d in darts)
    # A visit has three darts; a missed takeout can merge more, which never scores.
    regular = 0 < len(darts) <= 3
    summary = {
        name: int(regular and low <= points < high) for name, low, high in SCORE_BUCKETS
    }
    summary["scores_180"] = int(len(darts) == 3 and points == 180)
    return summary


def _takeout(state: dict[str, Any]) -> bool:
    """The Board Manager reports removal in its status or last event."""
    return any(
        "takeout" in str(state.get(key, "")).lower() for key in ("status", "event")
    )


def _key(dart: dict[str, Any]) -> tuple[int, int, str | None]:
    return dart["number"], dart["multiplier"], dart["name"]


def _contains(darts: list[dict[str, Any]], subset: list[dict[str, Any]]) -> bool:
    remaining = [_key(dart) for dart in darts]
    for dart in subset:
        if _key(dart) not in remaining:
            return False
        remaining.remove(_key(dart))
    return True


class TrainingSession:
    """A persistent session of observed darts, with one revisable active visit."""

    def __init__(self) -> None:
        self.started = dt_util.utcnow().isoformat()
        self._committed = dict.fromkeys(COUNTERS, 0)
        self._highest_visit = 0
        self._hits: Counter[str] = Counter()
        self._completed: list[tuple[str, dict[str, Any]]] = []
        self._active: list[dict[str, Any]] = []
        self._tracked: list[bool] = []
        self._initialized = False
        self._removing = False

    def restore(self, saved: dict[str, Any] | None) -> None:
        if not isinstance(saved, dict):
            return
        self._committed = {
            key: saved.get(key, 0)
            if type(saved.get(key)) is int and saved[key] >= 0
            else 0
            for key in COUNTERS
        }
        highest = saved.get("highest_visit")
        self._highest_visit = highest if type(highest) is int and highest >= 0 else 0
        hits = saved.get("hits")
        self._hits = Counter(
            {
                key: count
                for key, count in (hits.items() if isinstance(hits, dict) else [])
                if isinstance(key, str) and type(count) is int and count > 0
            }
        )
        started = saved.get("started")
        if isinstance(started, str):
            parsed: datetime | None = dt_util.parse_datetime(started)
            if parsed and parsed.tzinfo:
                self.started = started

    def _counted(self) -> list[dict[str, Any]]:
        return [
            dart
            for dart, tracked in zip(self._active, self._tracked, strict=True)
            if tracked
        ]

    def _contribution(self) -> dict[str, int]:
        darts = self._counted()
        return {
            "darts": len(darts),
            "points": sum(d["number"] * d["multiplier"] for d in darts),
            "doubles": sum(
                d["multiplier"] == 2 and 1 <= d["number"] <= 20 for d in darts
            ),
            "triples": sum(
                d["multiplier"] == 3 and 1 <= d["number"] <= 20 for d in darts
            ),
            "bulls": sum(
                d["number"] == 25 and d["multiplier"] in (1, 2) for d in darts
            ),
            "misses": sum(hit_key(d) == "MISS" for d in darts),
            "visits": int(bool(darts)),
            **_visit_summary(darts),
        }

    def snapshot(self) -> dict[str, Any]:
        current = self._contribution()
        hits = self._hits + Counter(map(hit_key, self._counted()))
        return {
            "started": self.started,
            **{key: self._committed[key] + current[key] for key in COUNTERS},
            "highest_visit": max(self._highest_visit, current["points"]),
            "hits": dict(sorted(hits.items())),
        }

    def _commit(self, announce: bool = False) -> None:
        darts = self._counted()
        current = self._contribution()
        for key in COUNTERS:
            self._committed[key] += current[key]
        self._highest_visit = max(self._highest_visit, current["points"])
        self._hits.update(map(hit_key, darts))
        if announce and darts:
            self._completed.append(
                (
                    "visit_completed",
                    {
                        "score": current["points"],
                        "darts": len(darts),
                        "segments": [d["name"] or hit_key(d) for d in darts],
                    },
                )
            )
        self._active = []
        self._tracked = []

    def _withdraw(self, observed: list[dict[str, Any]]) -> None:
        """Drop darts the board no longer reports, keeping the others' tracking."""
        remaining = list(zip(self._active, self._tracked, strict=True))
        tracked = []
        for dart in observed:
            index = next(i for i, (old, _) in enumerate(remaining) if old == dart)
            tracked.append(remaining.pop(index)[1])
        self._active, self._tracked = list(observed), tracked

    def baseline(self, state: dict[str, Any], announce: bool = False) -> None:
        """Keep accumulated counts; never count darts already present on startup."""
        self._commit(announce)
        observed = segments(state)
        self._initialized = observed is not None
        self._active = observed or []
        self._tracked = [False] * len(self._active)
        self._removing = False

    def reset(self, state: dict[str, Any]) -> None:
        self._committed = dict.fromkeys(COUNTERS, 0)
        self._highest_visit = 0
        self._hits = Counter()
        self._active, self._tracked = [], []
        self.started = dt_util.utcnow().isoformat()
        self.baseline(state)

    def observe(self, state: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        """Return dart events, preceded by a visit that ended with this state."""
        self._completed = []
        events = self._observe(state)
        return [*self._completed, *events]

    def _observe(self, state: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        observed = segments(state)
        if observed is None:
            return []
        status = str(state.get("status", "")).lower()
        if (
            not self._initialized
            or state.get("running") is not True
            or status in ("starting", "stopping", "stopped", "calibrating", "error")
        ):
            self.baseline(state, announce=self._initialized)
            return []
        if len(observed) < len(self._active):
            if not observed or _takeout(state):
                # Removing darts preserves their score, unlike a segment correction.
                self._commit(announce=True)
                self._active, self._tracked = observed, [False] * len(observed)
                self._removing = bool(observed)
                return []
            if _contains(self._active, observed):
                # Outside a takeout, fewer known darts mean a withdrawn detection.
                self._withdraw(observed)
                return []
            # New darts without an empty board in between: a missed takeout.
            self._commit(announce=True)
            self._active, self._tracked, self._removing = [], [], False
        if self._removing:
            if len(observed) <= len(self._active):
                self._active, self._tracked = observed, [False] * len(observed)
                return []
            # Darts beyond the ones still being removed are new throws.
            self._removing = False
        events = []
        for index, dart in enumerate(observed):
            kind = None
            if index >= len(self._active):
                self._active.append(dart)
                self._tracked.append(True)
                kind = "dart_detected"
            elif dart != self._active[index]:
                self._active[index] = dart
                kind = "dart_corrected"
            if kind:
                events.append(
                    (
                        kind,
                        {
                            "dart_index": index + 1,
                            "segment": dart["name"],
                            "score": dart["number"] * dart["multiplier"],
                        },
                    )
                )
        return events
