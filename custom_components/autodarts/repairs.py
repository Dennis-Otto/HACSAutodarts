"""Repairs that the integration can fix itself: calibrate a board on request."""

from __future__ import annotations

from typing import Any

from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError


class CalibrationFlow(RepairsFlow):
    """Many corrected darts: calibrate once the board is empty."""

    def __init__(self, entry_id: str) -> None:
        self._entry_id = entry_id

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="confirm")
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        loaded = entry is not None and entry.state is ConfigEntryState.LOADED
        coordinator = entry.runtime_data.local if entry and loaded else None
        if coordinator is None:
            return self.async_abort(reason="board_unavailable")
        try:
            await coordinator.async_recalibrate()
        except HomeAssistantError:
            return self.async_abort(reason="calibration_failed")
        return self.async_create_entry(data={})


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    return CalibrationFlow(str((data or {}).get("entry_id", "")))
