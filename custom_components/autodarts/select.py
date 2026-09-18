"""Camera standby duration supported by the Board Manager settings UI."""

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory

from .entity import AutodartsLocalEntity
from .local_api import STANDBY_MINUTES


async def async_setup_entry(hass, entry, async_add_entities):
    if coordinator := entry.runtime_data.local:
        async_add_entities([AutodartsStandbySelect(coordinator)])


class AutodartsStandbySelect(AutodartsLocalEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:timer-outline"
    _attr_options = [str(value) for value in STANDBY_MINUTES]

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "standby_minutes")

    @property
    def available(self) -> bool:
        return super().available and self.current_option is not None

    @property
    def current_option(self) -> str | None:
        value = (self.coordinator.data or {}).get("settings", {}).get("standby_minutes")
        return str(value) if value in STANDBY_MINUTES else None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_action(
            lambda: self.coordinator.client.set_standby_minutes(int(option))
        )
