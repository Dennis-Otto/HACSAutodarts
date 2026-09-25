"""Board software version and the update Board Manager 2 announces."""

from __future__ import annotations

from homeassistant.components.update import UpdateDeviceClass, UpdateEntity

from .entity import AutodartsLocalEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data.local
    if coordinator and coordinator.board_manager_2:
        async_add_entities([AutodartsBoardUpdate(coordinator)])


class AutodartsBoardUpdate(AutodartsLocalEntity, UpdateEntity):
    """Installing stays on the board PC (`autodarts update`); HA shows the news."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_title = "Autodarts Board Manager"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "board_software")

    @property
    def installed_version(self) -> str | None:
        return (self.coordinator.data or {}).get("version")

    @property
    def latest_version(self) -> str | None:
        system = (self.coordinator.data or {}).get("system") or {}
        return system.get("update_available") or self.installed_version
