"""Actions of the integration: start a practice game with one call."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .drills import DRILLS
from .local_coordinator import AutodartsLocalCoordinator
from .practice import GAMES, MAX_LEGS, MAX_PLAYERS, MAX_SETS, NAME_LENGTH

SERVICE_START_GAME = "start_game"
GAME_OPTIONS = [*(str(game) for game in GAMES), "cricket", *DRILLS]

START_GAME_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required("game"): vol.All(cv.string, vol.In(GAME_OPTIONS)),
        vol.Optional("players"): vol.All(
            cv.ensure_list,
            [vol.All(cv.string, vol.Length(max=NAME_LENGTH))],
            vol.Length(min=1, max=MAX_PLAYERS),
        ),
        vol.Optional("legs"): vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_LEGS)),
        vol.Optional("sets"): vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_SETS)),
        vol.Optional("double_out"): cv.boolean,
    }
)


def _coordinator(
    hass: HomeAssistant, entry_id: str | None
) -> AutodartsLocalCoordinator:
    """The board of the given entry, or the only local board there is."""
    if entry_id:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="unknown_board"
            )
        entries = [entry]
    else:
        entries = hass.config_entries.async_entries(DOMAIN)
    boards: list[AutodartsLocalCoordinator] = [
        entry.runtime_data.local
        for entry in entries
        if entry.state is ConfigEntryState.LOADED and entry.runtime_data.local
    ]
    if not boards:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="no_board"
        )
    if len(boards) > 1:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="several_boards"
        )
    return boards[0]


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    async def start_game(call: ServiceCall) -> None:
        coordinator = _coordinator(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        game: str = call.data["game"]
        await coordinator.async_start_game(
            int(game) if game.isdigit() else game,
            names=call.data.get("players"),
            legs=call.data.get("legs"),
            sets=call.data.get("sets"),
            double_out=call.data.get("double_out"),
        )

    hass.services.async_register(
        DOMAIN, SERVICE_START_GAME, start_game, schema=START_GAME_SCHEMA
    )
