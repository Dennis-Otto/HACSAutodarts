"""Data update coordinator for Autodarts."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    AutodartsApiError,
    AutodartsAuthError,
    AutodartsCloudClient,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AutodartsDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch cloud match data independently of the local Board Manager."""

    def __init__(
        self,
        hass: HomeAssistant,
        cloud: AutodartsCloudClient,
        board_id: str,
        entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=entry,
        )
        self.cloud = cloud
        self.board_id = board_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch board and match data from the cloud API."""
        result: dict[str, Any] = {
            "board": {},
            "match": None,
            "local": {},
        }

        # 1. Cloud: get board state (includes matchId)
        try:
            board = await self.cloud.get_board(self.board_id)
            result["board"] = board
        except AutodartsAuthError as err:
            raise ConfigEntryAuthFailed(
                "Autodarts account must be linked again"
            ) from err
        except AutodartsApiError as err:
            raise UpdateFailed(f"Error fetching board data: {err}") from err

        # 2. Cloud: if a match is active, fetch match data + live state
        match_id = board.get("matchId")
        if match_id:
            try:
                match = await self.cloud.get_match(match_id)
                # Merge live game state into match dict
                try:
                    state = await self.cloud.get_match_state(match_id)
                    match.update(state)
                except AutodartsAuthError:
                    raise
                except AutodartsApiError:
                    _LOGGER.debug("Could not fetch match state for %s", match_id)
                result["match"] = match
            except AutodartsAuthError as err:
                raise ConfigEntryAuthFailed(
                    "Autodarts account must be linked again"
                ) from err
            except AutodartsApiError as err:
                _LOGGER.warning("Could not fetch match %s: %s", match_id, err)

        return result
