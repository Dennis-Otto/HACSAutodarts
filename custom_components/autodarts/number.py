"""How long a training session may pause before it ends by itself."""

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import AutodartsLocalEntity
from .local_coordinator import AutodartsLocalCoordinator
from .runtime import AutodartsConfigEntry
from .training import IDLE_MINUTES_MAX

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AutodartsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    if coordinator := entry.runtime_data.local:
        async_add_entities([AutodartsIdleTimeout(coordinator)])


class AutodartsIdleTimeout(AutodartsLocalEntity, NumberEntity):
    """Minutes without darts before a session ends; 0 keeps it running."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_native_min_value = 0
    _attr_native_max_value = IDLE_MINUTES_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: AutodartsLocalCoordinator) -> None:
        super().__init__(coordinator, "training_idle_timeout")

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> int:
        return self.coordinator.training.idle_minutes

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_idle_minutes(int(value))
