"""Explicit local Board Manager actions, also usable by HA automations."""

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import callback

from .entity import AutodartsLocalEntity

BUTTONS = {
    "start": ("mdi:play", True),
    "stop": ("mdi:stop", True),
    "reset": ("mdi:restore", True),
    "restart": ("mdi:restart", True),
    "calibrate": ("mdi:bullseye-arrow", True),
    "connect": ("mdi:cloud-check", False),
    "disconnect": ("mdi:cloud-off-outline", False),
    "start_streams": ("mdi:video", False),
    "stop_streams": ("mdi:video-off", False),
}
# Board Manager 2 has no routes to connect or disconnect its cloud link.
V1_ONLY = ("connect", "disconnect")


async def async_setup_entry(hass, entry, async_add_entities):
    if coordinator := entry.runtime_data.local:
        unsupported = V1_ONLY if coordinator.board_manager_2 else ()
        async_add_entities(
            [
                AutodartsButton(coordinator, key)
                for key in BUTTONS
                if key not in unsupported
            ]
            + [AutodartsTrainingReset(coordinator)]
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
                        AutodartsCameraCalibration(coordinator, index)
                        for index in sorted(new)
                    ]
                )

        discover_cameras()
        entry.async_on_unload(coordinator.async_add_listener(discover_cameras))


class AutodartsButton(AutodartsLocalEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, command: str) -> None:
        super().__init__(coordinator, command)
        self._command = command
        self._attr_icon, self._attr_entity_registry_enabled_default = BUTTONS[command]

    async def async_press(self) -> None:
        await self.coordinator.async_action(
            lambda: self.coordinator.client.command(self._command)
        )


class AutodartsCameraCalibration(AutodartsLocalEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:camera-iris"

    def __init__(self, coordinator, index: int) -> None:
        super().__init__(coordinator, f"calibrate_camera_{index}")
        self._index = index
        self._attr_translation_key = "calibrate_camera"
        self._attr_translation_placeholders = {"number": str(index + 1)}

    @property
    def available(self) -> bool:
        return super().available and self._index < (self.coordinator.data or {}).get(
            "settings", {}
        ).get("camera_count", 0)

    async def async_press(self) -> None:
        await self.coordinator.async_action(
            lambda: self.coordinator.client.calibrate_camera(self._index)
        )


class AutodartsTrainingReset(AutodartsLocalEntity, ButtonEntity):
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "reset_training")

    @property
    def available(self) -> bool:
        return True

    async def async_press(self) -> None:
        await self.coordinator.async_reset_training()
