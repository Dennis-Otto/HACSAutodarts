"""Explicit local Board Manager actions, also usable by HA automations."""

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

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


async def async_setup_entry(hass, entry, async_add_entities):
    if coordinator := entry.runtime_data.local:
        async_add_entities([AutodartsButton(coordinator, key) for key in BUTTONS])


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
