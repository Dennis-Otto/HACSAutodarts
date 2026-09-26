"""Board cameras: live streams from Board Manager 2, otherwise snapshots.

To show a camera, the integration never starts or stops the detection or the
camera streams.
"""

from aiohttp import hdrs, web
from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_aiohttp_proxy_stream
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import AutodartsLocalEntity
from .errors import AutodartsApiError
from .local_coordinator import AutodartsLocalCoordinator
from .runtime import AutodartsConfigEntry

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AutodartsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    if coordinator := entry.runtime_data.local:
        known: set[int] = set()

        @callback
        def discover_cameras() -> None:
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

    def __init__(self, coordinator: AutodartsLocalCoordinator, index: int) -> None:
        Camera.__init__(self)
        AutodartsLocalEntity.__init__(self, coordinator, f"camera_{index}")
        self._attr_translation_key = "board_camera"
        self._attr_translation_placeholders = {"number": str(index + 1)}
        self._attr_extra_state_attributes = {"camera": index + 1}
        self._index = index

    @property
    def available(self) -> bool:
        count = (self.coordinator.data or {}).get("settings", {}).get("camera_count", 0)
        return super().available and self._index < count

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        try:
            return await self.coordinator.client.get_camera_image(self._index)
        except AutodartsApiError:
            return None

    async def handle_async_mjpeg_stream(
        self, request: web.Request
    ) -> web.StreamResponse | None:
        """Relay the live stream of Board Manager 2; fall back to snapshots."""
        if self.coordinator.board_manager_2:
            try:
                stream = await self.coordinator.client.open_camera_stream(self._index)
            except AutodartsApiError:
                pass
            else:
                try:
                    return await async_aiohttp_proxy_stream(
                        self.hass,
                        request,
                        stream.content,
                        stream.headers.get(hdrs.CONTENT_TYPE),
                    )
                finally:
                    stream.close()
        return await super().handle_async_mjpeg_stream(request)
