"""Count observed local darts, including corrections, without replaying snapshots."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

COUNTERS = ("darts", "triples", "bulls", "scores_180", "points")


def segments(state: dict) -> list[dict] | None:
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


class TrainingSession:
    """A persistent session of observed darts, with one revisable active visit."""

    def __init__(self) -> None:
        self.started = dt_util.utcnow().isoformat()
        self._committed = dict.fromkeys(COUNTERS, 0)
        self._active: list[dict] = []
        self._tracked: list[bool] = []
        self._initialized = False
        self._removing = False

    def restore(self, saved: dict | None) -> None:
        if not isinstance(saved, dict):
            return
        self._committed = {
            key: saved.get(key, 0)
            if type(saved.get(key)) is int and saved[key] >= 0
            else 0
            for key in COUNTERS
        }
        started = saved.get("started")
        if isinstance(started, str):
            parsed: datetime | None = dt_util.parse_datetime(started)
            if parsed and parsed.tzinfo:
                self.started = started

    def _contribution(self) -> dict[str, int]:
        darts = [
            dart
            for dart, tracked in zip(self._active, self._tracked, strict=True)
            if tracked
        ]
        return {
            "darts": len(darts),
            "triples": sum(
                d["multiplier"] == 3 and 1 <= d["number"] <= 20 for d in darts
            ),
            "bulls": sum(
                d["number"] == 25 and d["multiplier"] in (1, 2) for d in darts
            ),
            "scores_180": int(
                len(darts) == 3
                and all(d["number"] == 20 and d["multiplier"] == 3 for d in darts)
            ),
            "points": sum(d["number"] * d["multiplier"] for d in darts),
        }

    def snapshot(self) -> dict[str, Any]:
        current = self._contribution()
        return {
            "started": self.started,
            **{key: self._committed[key] + current[key] for key in COUNTERS},
        }

    def _commit(self) -> None:
        current = self._contribution()
        for key in COUNTERS:
            self._committed[key] += current[key]
        self._active = []
        self._tracked = []

    def baseline(self, state: dict) -> None:
        """Keep accumulated counts; never count darts already present on startup."""
        self._commit()
        observed = segments(state)
        self._initialized = observed is not None
        self._active = observed or []
        self._tracked = [False] * len(self._active)
        self._removing = False

    def reset(self, state: dict) -> None:
        self._committed = dict.fromkeys(COUNTERS, 0)
        self._active, self._tracked = [], []
        self.started = dt_util.utcnow().isoformat()
        self.baseline(state)

    def observe(self, state: dict) -> list[tuple[str, dict]]:
        observed = segments(state)
        if observed is None:
            return []
        status = str(state.get("status", "")).lower()
        if (
            not self._initialized
            or state.get("running") is not True
            or status in ("starting", "stopping", "stopped", "calibrating", "error")
        ):
            self.baseline(state)
            return []
        # Removing darts preserves their score, unlike a segment correction.
        if len(observed) < len(self._active):
            self._commit()
            self._active, self._tracked = observed, [False] * len(observed)
            self._removing = bool(observed)
            return []
        if self._removing:
            return []
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
