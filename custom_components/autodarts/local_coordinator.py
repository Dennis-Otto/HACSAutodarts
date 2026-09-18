"""Update the local board independently from cloud credentials and outages."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Coroutine
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .errors import AutodartsApiError
from .local_api import AutodartsLocalClient

_LOGGER = logging.getLogger(__name__)


class AutodartsLocalCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll local status and expose only sanitized settings and diagnostics."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AutodartsLocalClient,
        board_id: str,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_local",
            config_entry=entry,
            update_interval=timedelta(seconds=2),
        )
        self.client = client
        self.board_id = board_id
        self.device_name = "Autodarts Board"
        self._settings: dict[str, Any] = {}
        self._version: str | None = None
        self._metadata_updated = 0.0
        self._action_lock = asyncio.Lock()

    async def _optional(self, operation: Coroutine) -> Any:
        try:
            return await operation
        except AutodartsApiError:
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            state = await self.client.get_state()
        except AutodartsApiError as err:
            raise UpdateFailed("Local Board Manager unavailable") from err
        stats, camera_stats = await asyncio.gather(
            self._optional(self.client.get_stats()),
            self._optional(self.client.get_camera_stats()),
        )
        if (
            not self._metadata_updated
            or time.monotonic() - self._metadata_updated >= 30
        ):
            config, version = await asyncio.gather(
                self._optional(self.client.get_config()),
                self._optional(self.client.get_version()),
            )
            if config and config.get("board_id", self.board_id) != self.board_id:
                raise UpdateFailed("Local address belongs to a different board")
            # Do not expose stale settings as current if the config endpoint fails.
            self._settings = config or {}
            self._version = version or self._version
            self._metadata_updated = time.monotonic()
        return {
            "local": state,
            "settings": self._settings,
            "version": self._version,
            "stats": stats or {},
            "camera_stats": camera_stats or {},
        }

    async def async_action(
        self, action: Callable[[], Coroutine[Any, Any, None]]
    ) -> None:
        """Surface rejected commands to HA and refresh state after success."""
        async with self._action_lock:
            try:
                await action()
            except AutodartsApiError as err:
                raise HomeAssistantError(
                    "Local board action failed. Check the board connection and Board Manager."
                ) from err
            self._metadata_updated = 0
            await self.async_request_refresh()
