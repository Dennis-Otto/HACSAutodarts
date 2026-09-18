"""Local detection, upstream connection and automatic calibration settings."""

from functools import partial

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory

from .entity import AutodartsLocalEntity
from .local_api import CONFIG_SWITCHES


async def async_setup_entry(hass, entry, async_add_entities):
    if coordinator := entry.runtime_data.local:
        async_add_entities(
            [
                AutodartsSwitch(coordinator, key)
                for key in ("detection", "upstream", *CONFIG_SWITCHES)
            ]
        )


class AutodartsSwitch(AutodartsLocalEntity, SwitchEntity):
    def __init__(self, coordinator, key: str) -> None:
        super().__init__(coordinator, key)
        self._key = key
        self._attr_icon = (
            "mdi:bullseye"
            if key == "detection"
            else "mdi:cloud"
            if key == "upstream"
            else "mdi:auto-fix"
        )
        if key in CONFIG_SWITCHES:
            self._attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        return super().available and self.is_on is not None

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        if self._key in CONFIG_SWITCHES:
            return data.get("settings", {}).get(self._key)
        value = data.get("local", {}).get(
            "running" if self._key == "detection" else "connected"
        )
        return value if isinstance(value, bool) else None

    async def _async_set(self, enabled: bool) -> None:
        client = self.coordinator.client
        if self._key == "detection":
            action = partial(client.command, "start" if enabled else "stop")
        elif self._key == "upstream":
            action = partial(client.command, "connect" if enabled else "disconnect")
        else:
            action = partial(client.set_config_switch, self._key, enabled)
        await self.coordinator.async_action(action)

    async def async_turn_on(self, **kwargs) -> None:
        await self._async_set(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._async_set(False)
