"""Sensor platform for the Autodarts integration."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfInformation
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    SENSOR_BOARD_EVENT,
    SENSOR_BOARD_STATUS,
    SENSOR_DARTS_THROWN,
    SENSOR_GAME_MODE,
    SENSOR_LAST_THROW,
    SENSOR_MATCH_STATE,
    SENSOR_NUM_THROWS,
    SENSOR_ROUND,
    SENSOR_VISIT_SCORE,
)
from .coordinator import AutodartsDataUpdateCoordinator
from .entity import AutodartsEntity, AutodartsLocalEntity
from .training import COUNTERS

PARALLEL_UPDATES = 0

# Board Manager detection states, translated in strings.json.
LOCAL_STATES = [
    "offline",
    "starting",
    "stopping",
    "stopped",
    "throw",
    "takeout",
    "takeout_in_progress",
    "calibrating",
    "error",
]
MATCH_STATES = ["no_match", "active", "finished"]
BOARD_STATES = ["connected", "disconnected"]

# ---------------------------------------------------------------------------
# Helpers to extract values from coordinator data
# ---------------------------------------------------------------------------
# coordinator.data = {"board": {...}, "match": {...} | None, "local": {...}}


def _board(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("board") or {}


def _match(data: dict[str, Any]) -> dict[str, Any] | None:
    return data.get("match")


def _local(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("local") or {}


# -- value extractors -------------------------------------------------------


def _get_board_status(data: dict[str, Any]) -> str:
    """Board connected / disconnected (from cloud board state)."""
    board = _board(data)
    state = board.get("state") or {}
    if state.get("connected"):
        return "connected"
    return "disconnected"


def _get_board_event(data: dict[str, Any]) -> str | None:
    """Last board event from local detection or cloud."""
    local = _local(data)
    if local:
        return local.get("event") or local.get("status")
    board = _board(data)
    state = board.get("state") or {}
    return state.get("event") or board.get("status")


def _get_game_mode(data: dict[str, Any]) -> str | None:
    """Game variant (X01, Cricket, etc.) from match."""
    match = _match(data)
    if not match:
        return None
    return match.get("variant")


def _get_match_state(data: dict[str, Any]) -> str | None:
    """Match state — active / finished / etc."""
    match = _match(data)
    if not match:
        return "no_match"
    if match.get("finished"):
        return "finished"
    return "active"


def _get_round(data: dict[str, Any]) -> int | None:
    """Current round number."""
    match = _match(data)
    if not match:
        return None
    return match.get("round")


BEDS = frozenset(
    {"Single", "SingleInner", "SingleOuter", "Double", "Triple", "Outside"}
)
SEGMENT_KEYS = ("segment", "number", "multiplier", "bed")


def _dart(dart: Any) -> dict[str, Any] | None:
    """A dart's scoring segment and normalized board position for dashboards."""
    segment = dart.get("segment") if isinstance(dart, dict) else None
    if not isinstance(segment, dict):
        return None
    number, multiplier = segment.get("number"), segment.get("multiplier")
    if type(number) is not int or type(multiplier) is not int:
        return None
    result = {
        "segment": segment["name"] if isinstance(segment.get("name"), str) else None,
        "number": number,
        "multiplier": multiplier,
        "score": number * multiplier,
        "bed": segment["bed"] if segment.get("bed") in BEDS else None,
    }
    coords = dart.get("coords")
    if isinstance(coords, dict) and all(
        type(coords.get(axis)) in (int, float) and math.isfinite(coords[axis])
        for axis in ("x", "y")
    ):
        # 1.0 is the outer edge of the double ring; y points to the 20.
        result["x"], result["y"] = round(coords["x"], 3), round(coords["y"], 3)
    return result


def _darts(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Valid darts of the current visit; malformed board data is ignored."""
    throws = _local(data).get("throws")
    return list(filter(None, map(_dart, throws if isinstance(throws, list) else [])))


def _get_last_throw(data: dict[str, Any]) -> str | None:
    """Last detected throw segment name (e.g. T20, D16, S5, M2)."""
    darts = _darts(data)
    return darts[-1]["segment"] if darts else None


def _number(value: Any) -> int | float | None:
    """A board value a numeric sensor can show; anything else reads as unknown."""
    if type(value) in (int, float) and math.isfinite(value):
        return value
    return None


def _get_num_throws(data: dict[str, Any]) -> int | None:
    """Number of throws in the current turn (from local board, 0–3)."""
    local = _local(data)
    if local:
        return _number(local.get("numThrows"))
    return None


def _get_visit_score(data: dict[str, Any]) -> int | None:
    """Total score of the current turn/visit."""
    match = _match(data)
    if not match:
        return None
    return match.get("turnScore")


def _get_darts_thrown(data: dict[str, Any]) -> int | None:
    """Total darts thrown in the match (across all players)."""
    match = _match(data)
    if not match:
        return None
    turns = match.get("turns")
    if isinstance(turns, list):
        return sum(len(t.get("throws", [])) for t in turns)
    return None


# ---------------------------------------------------------------------------
# Sensor descriptions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class AutodartsSensorEntityDescription(SensorEntityDescription):
    """Describe an Autodarts sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


STATIC_SENSORS: tuple[AutodartsSensorEntityDescription, ...] = (
    AutodartsSensorEntityDescription(
        key=SENSOR_BOARD_STATUS,
        translation_key=SENSOR_BOARD_STATUS,
        device_class=SensorDeviceClass.ENUM,
        options=BOARD_STATES,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get_board_status,
    ),
    AutodartsSensorEntityDescription(
        key=SENSOR_BOARD_EVENT,
        translation_key=SENSOR_BOARD_EVENT,
        value_fn=_get_board_event,
    ),
    AutodartsSensorEntityDescription(
        key=SENSOR_GAME_MODE,
        translation_key=SENSOR_GAME_MODE,
        value_fn=_get_game_mode,
    ),
    AutodartsSensorEntityDescription(
        key=SENSOR_MATCH_STATE,
        translation_key=SENSOR_MATCH_STATE,
        device_class=SensorDeviceClass.ENUM,
        options=MATCH_STATES,
        value_fn=_get_match_state,
    ),
    AutodartsSensorEntityDescription(
        key=SENSOR_ROUND,
        translation_key=SENSOR_ROUND,
        value_fn=_get_round,
    ),
    AutodartsSensorEntityDescription(
        key=SENSOR_LAST_THROW,
        translation_key=SENSOR_LAST_THROW,
        value_fn=_get_last_throw,
    ),
    AutodartsSensorEntityDescription(
        key=SENSOR_NUM_THROWS,
        translation_key=SENSOR_NUM_THROWS,
        native_unit_of_measurement="darts",
        value_fn=_get_num_throws,
    ),
    AutodartsSensorEntityDescription(
        key=SENSOR_VISIT_SCORE,
        translation_key=SENSOR_VISIT_SCORE,
        native_unit_of_measurement="points",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_visit_score,
    ),
    AutodartsSensorEntityDescription(
        key=SENSOR_DARTS_THROWN,
        translation_key=SENSOR_DARTS_THROWN,
        native_unit_of_measurement="darts",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_get_darts_thrown,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Autodarts sensors from a config entry."""
    runtime = entry.runtime_data
    entities: list[SensorEntity] = []
    local_keys = {SENSOR_BOARD_EVENT, SENSOR_LAST_THROW, SENSOR_NUM_THROWS}
    if runtime.cloud:
        entities.extend(
            AutodartsSensor(runtime.cloud, description)
            for description in STATIC_SENSORS
            if runtime.local is None or description.key not in local_keys
        )
    if runtime.local:
        entities.extend(
            AutodartsTrainingSensor(runtime.local, key)
            for key in (*COUNTERS, "started")
        )
        entities.extend(
            AutodartsLocalSensor(runtime.local, description)
            for description in STATIC_SENSORS
            if description.key in local_keys
        )
        if runtime.local.board_manager_2:
            entities.extend(
                AutodartsLocalSensor(runtime.local, description)
                for description in SYSTEM_SENSORS
            )
        entities.extend(
            (
                AutodartsVisitSensor
                if description.key == "local_visit_score"
                else AutodartsLocalSensor
            )(runtime.local, description)
            for description in LOCAL_SENSORS
        )
    async_add_entities(entities)
    if coordinator := runtime.local:
        known: set[int] = set()

        @callback
        def discover_cameras():
            count = (coordinator.data or {}).get("settings", {}).get("camera_count", 0)
            new = set(range(count)) - known
            if not new:
                return
            known.update(new)
            async_add_entities(
                [
                    AutodartsLocalSensor(
                        coordinator,
                        AutodartsSensorEntityDescription(
                            key=f"camera_{index}_fps",
                            translation_key="camera_fps",
                            translation_placeholders={"number": str(index + 1)},
                            native_unit_of_measurement="fps",
                            entity_category=EntityCategory.DIAGNOSTIC,
                            entity_registry_enabled_default=False,
                            value_fn=lambda data, i=index: _camera_fps(data, i),
                        ),
                    )
                    for index in sorted(new)
                ]
            )

        discover_cameras()
        entry.async_on_unload(coordinator.async_add_listener(discover_cameras))


# ---------------------------------------------------------------------------
# Sensor entity classes
# ---------------------------------------------------------------------------


class AutodartsSensor(AutodartsEntity, SensorEntity):
    """Representation of a static Autodarts sensor."""

    entity_description: AutodartsSensorEntityDescription

    def __init__(
        self,
        coordinator: AutodartsDataUpdateCoordinator,
        description: AutodartsSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.board_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data or {})


def _last_throw_score(data: dict[str, Any]) -> int | None:
    darts = _darts(data)
    return darts[-1]["score"] if darts else None


def _local_visit_score(data: dict[str, Any]) -> int:
    return sum(dart["score"] for dart in _darts(data))


def _local_status(data: dict[str, Any]) -> str | None:
    """Board Manager status as a translatable state; unknown ones read as unknown."""
    status = _local(data).get("status")
    if not isinstance(status, str):
        return None
    state = "_".join(status.lower().split())
    return state if state in LOCAL_STATES else None


def _camera_fps(data: dict[str, Any], index: int) -> float | None:
    fps = data.get("camera_stats", {}).get("fps")
    return _number(fps[index]) if isinstance(fps, list) and index < len(fps) else None


LOCAL_SENSORS = (
    AutodartsSensorEntityDescription(
        key="local_status",
        translation_key="local_status",
        device_class=SensorDeviceClass.ENUM,
        options=LOCAL_STATES,
        value_fn=_local_status,
    ),
    AutodartsSensorEntityDescription(
        key="last_throw_score",
        translation_key="last_throw_score",
        native_unit_of_measurement="points",
        value_fn=_last_throw_score,
    ),
    AutodartsSensorEntityDescription(
        key="local_visit_score",
        translation_key="local_visit_score",
        native_unit_of_measurement="points",
        value_fn=_local_visit_score,
    ),
    AutodartsSensorEntityDescription(
        key="detection_fps",
        translation_key="detection_fps",
        native_unit_of_measurement="fps",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _number(data.get("stats", {}).get("fps")),
    ),
)


def _system(data: dict[str, Any], key: str) -> int | float | None:
    return _number((data.get("system") or {}).get(key))


# Host load reported by Board Manager 2.
SYSTEM_SENSORS = (
    AutodartsSensorEntityDescription(
        key="cpu_usage",
        translation_key="cpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _system(data, "cpu_percent"),
    ),
    AutodartsSensorEntityDescription(
        key="memory_usage",
        translation_key="memory_usage",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.MEBIBYTES,
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _system(data, "memory_bytes"),
    ),
)


class AutodartsLocalSensor(AutodartsLocalEntity, SensorEntity):
    def __init__(
        self, coordinator, description: AutodartsSensorEntityDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_translation_key = description.translation_key

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})


class AutodartsVisitSensor(AutodartsLocalSensor):
    """The detected visit, with each dart's segment and position for cards."""

    # Live positions are for display only and must not grow the recorder database.
    _unrecorded_attributes = frozenset({"throws"})

    def __init__(
        self, coordinator, description: AutodartsSensorEntityDescription
    ) -> None:
        super().__init__(coordinator, description)
        self._throws: list[dict[str, Any]] = []
        self._update_throws()

    def _update_throws(self) -> None:
        throws = []
        for dart in _darts(self.coordinator.data or {}):
            previous = (
                self._throws[len(throws)] if len(throws) < len(self._throws) else {}
            )
            if all(previous.get(key) == dart[key] for key in SEGMENT_KEYS):
                # Camera jitter moves an unchanged dart slightly; keep it steady.
                dart |= {
                    axis: previous[axis] for axis in ("x", "y") if axis in previous
                }
            throws.append(dart)
        self._throws = throws

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_throws()
        super()._handle_coordinator_update()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"throws": self._throws}


class AutodartsTrainingSensor(AutodartsLocalEntity, SensorEntity):
    """Locally stored session totals remain readable while the board is offline."""

    def __init__(self, coordinator, key: str) -> None:
        super().__init__(coordinator, f"training_{key}")
        self._key = key
        if key == "started":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        else:
            # Totals only grow until the session is reset, like a meter.
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self):
        value = self.coordinator.training.snapshot()[self._key]
        return dt_util.parse_datetime(value) if self._key == "started" else value
