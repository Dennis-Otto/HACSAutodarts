"""Connectivity to the local manager, distinct from its cloud connection."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import callback

from .entity import AutodartsLocalEntity

MOTION_SENSORS = {
    "hand_detected": "isHand",
    "image_stable": "isStable",
    "takeout_partial": "isTakeoutPartial",
    "takeout_full": "isTakeoutFull",
}


async def async_setup_entry(hass, entry, async_add_entities):
    if coordinator := entry.runtime_data.local:
        async_add_entities(
            [AutodartsLocalConnectivity(coordinator)]
            + [
                AutodartsLocalState(coordinator, key)
                for key in (
                    *MOTION_SENSORS,
                    "cameras_active",
                    "calibrating",
                    "realtime_connected",
                    "camera_problem",
                )
            ]
        )
        known: set[int] = set()

        @callback
        def discover_cameras():
            count = (coordinator.data or {}).get("settings", {}).get("camera_count", 0)
            new = set(range(count)) - known
            if new:
                known.update(new)
                async_add_entities(
                    [
                        AutodartsLocalState(coordinator, "camera_problem", index)
                        for index in sorted(new)
                    ]
                )

        discover_cameras()
        entry.async_on_unload(coordinator.async_add_listener(discover_cameras))


class AutodartsLocalConnectivity(AutodartsLocalEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "local_connected")

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success


class AutodartsLocalState(AutodartsLocalEntity, BinarySensorEntity):
    def __init__(self, coordinator, key: str, index: int | None = None) -> None:
        super().__init__(
            coordinator, key if index is None else f"camera_{index}_problem"
        )
        self._key, self._index = key, index
        if key == "camera_problem":
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        elif key == "realtime_connected":
            self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if index is not None:
            self._attr_translation_key = "individual_camera_problem"
            self._attr_translation_placeholders = {"number": str(index + 1)}

    @property
    def available(self) -> bool:
        if self._key == "realtime_connected":
            return True
        return super().available and self.is_on is not None

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        state = data.get("local", {})
        if self._key in MOTION_SENSORS:
            if state.get("running") is False or str(
                state.get("status", "")
            ).lower() in ("starting", "stopping", "stopped", "calibrating", "error"):
                return False
            return data.get("motion", {}).get(MOTION_SENSORS[self._key])
        if self._key == "cameras_active":
            return data.get("camera_state", {}).get("isRunning")
        if self._key == "calibrating":
            status = state.get("status")
            return status.lower() == "calibrating" if isinstance(status, str) else None
        if self._key == "realtime_connected":
            return self.coordinator.stream_connected
        problems = data.get("camera_problems", [])
        if self._index is not None:
            return problems[self._index] if self._index < len(problems) else None
        if any(problem is True for problem in problems):
            return True
        return (
            False
            if problems and all(problem is False for problem in problems)
            else None
        )
