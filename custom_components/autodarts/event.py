"""Native HA events for observed darts, corrections and takeout transitions."""

from homeassistant.components.event import EventEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .entity import AutodartsLocalEntity
from .local_coordinator import EVENT_TYPES

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    if coordinator := entry.runtime_data.local:
        async_add_entities([AutodartsBoardEvent(coordinator)])


class AutodartsBoardEvent(AutodartsLocalEntity, EventEntity):
    _attr_event_types = EVENT_TYPES

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "board_events")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self.coordinator.event_signal, self._receive
            )
        )

    @callback
    def _receive(self, kind: str, attributes: dict) -> None:
        self._trigger_event(kind, attributes)
        self.async_write_ha_state()
