"""Optional camera snapshots. Viewing never starts/stops detection or streaming."""

from homeassistant.components.camera import Camera
from homeassistant.core import callback

from .entity import AutodartsLocalEntity
from .errors import AutodartsApiError


async def async_setup_entry(hass, entry, async_add_entities):
    if coordinator := entry.runtime_data.local:
        known: set[int] = set()

        @callback
        def discover_cameras():
            count = (coordinator.data or {}).get("settings", {}).get("camera_count", 0)
            new = set(range(count)) - known
            if not new:
                return
            known.update(new)
            async_add_entities(
                [AutodartsCamera(coordinator, index) for index in sorted(new)]
            )

        discover_cameras()
        entry.async_on_unload(coordinator.async_add_listener(discover_cameras))


class AutodartsCamera(AutodartsLocalEntity, Camera):
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "board_camera"

    def __init__(self, coordinator, index: int) -> None:
        Camera.__init__(self)
        AutodartsLocalEntity.__init__(self, coordinator, f"camera_{index}")
        self._attr_translation_key = "board_camera"
        self._attr_translation_placeholders = {"number": str(index + 1)}
        self._index = index

    @property
    def available(self) -> bool:
        count = (self.coordinator.data or {}).get("settings", {}).get("camera_count", 0)
        return super().available and self._index < count

    async def async_camera_image(self, width=None, height=None) -> bytes | None:
        try:
            return await self.coordinator.client.get_camera_image(self._index)
        except AutodartsApiError:
            return None
