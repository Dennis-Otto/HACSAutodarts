"""The X01 practice game in Home Assistant: entities, events and restarts."""

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .local_helpers import local_entry_data, mock_board
from .test_local_setup import entity_id, setup_local, state
from .test_sessions import record, switch
from .test_training import BULL, OUTER_BULL, T20, board

D18 = ("D18", 18, 2)


async def select_game(hass, option: str) -> None:
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_id(hass, "select", "practice_game"), "option": option},
        blocking=True,
    )
    await hass.async_block_till_done()


async def throw(hass, coordinator, *darts) -> None:
    """Throw a visit dart by dart, then pull the darts."""
    for count in range(1, len(darts) + 1):
        coordinator.async_receive("state", board(*darts[:count]))
    coordinator.async_receive("state", board())
    await hass.async_block_till_done()


async def test_practice_game_counts_down_busts_and_wins(
    hass, aioclient_mock, hass_storage
):
    entry = await setup_local(hass, aioclient_mock, state=board())
    coordinator = entry.runtime_data.local
    events = record(hass, coordinator)
    assert state(hass, "select", "practice_game") == "off"
    assert state(hass, "sensor", "practice_remaining") == "unknown"
    assert state(hass, "sensor", "practice_checkout") == "unknown"

    await select_game(hass, "301")
    assert state(hass, "sensor", "practice_remaining") == "301"
    await throw(hass, coordinator, T20, T20, T20)
    assert state(hass, "sensor", "practice_remaining") == "121"
    assert state(hass, "sensor", "practice_checkout") == "T20 25 D18"

    # 121 - 120 leaves one, which cannot be finished on a double.
    await throw(hass, coordinator, T20, T20)
    busts = [attributes for kind, attributes in events if kind == "bust"]
    assert len(busts) == 1
    assert busts[0]["game"] == 301 and busts[0]["remaining"] == 121
    assert state(hass, "sensor", "practice_remaining") == "121"

    await throw(hass, coordinator, T20, OUTER_BULL, D18)
    won = [attributes for kind, attributes in events if kind == "leg_won"]
    assert len(won) == 1
    assert {key: won[0][key] for key in ("game", "darts", "average", "checkout")} == {
        "game": 301,
        "darts": 8,
        "average": 112.88,
        "checkout": 121,
    }
    remaining = hass.states.get(entity_id(hass, "sensor", "practice_remaining"))
    assert remaining.state == "301"
    assert remaining.attributes["legs"][0]["darts"] == 8

    registry = er.async_get(hass)
    double_out = registry.async_get(entity_id(hass, "switch", "practice_double_out"))
    assert double_out.entity_category == er.EntityCategory.CONFIG
    await switch(hass, "practice_double_out", False)
    assert state(hass, "switch", "practice_double_out") == "off"
    await throw(hass, coordinator, BULL)
    assert state(hass, "sensor", "practice_remaining") == "251"
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": entity_id(hass, "button", "practice_new_leg")},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert state(hass, "sensor", "practice_remaining") == "301"
    # Settings and the new leg are saved at once, with the finished legs.
    saved = hass_storage[f"autodarts.{entry.entry_id}.training"]["data"]["practice"]
    assert saved["game"] == 301 and saved["double_out"] is False
    assert saved["legs"][0]["checkout"] == 121
    await select_game(hass, "off")
    assert state(hass, "sensor", "practice_remaining") == "unknown"


async def test_practice_game_survives_a_restart(hass, aioclient_mock, hass_storage):
    data = local_entry_data()
    hass_storage["autodarts.practice-entry.training"] = {
        "version": 1,
        "key": "autodarts.practice-entry.training",
        "data": {
            "practice": {
                "game": 501,
                "double_out": True,
                "remaining": 100,
                "darts": 30,
                "legs": [{"game": 501, "darts": 18, "average": 83.5, "checkout": 40}],
            }
        },
    }
    mock_board(aioclient_mock, state=board())
    entry = MockConfigEntry(
        domain="autodarts", version=2, data=data, entry_id="practice-entry"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert state(hass, "select", "practice_game") == "501"
    remaining = hass.states.get(entity_id(hass, "sensor", "practice_remaining"))
    assert remaining.state == "100"
    assert remaining.attributes["darts"] == 30
    assert len(remaining.attributes["legs"]) == 1
    assert state(hass, "sensor", "practice_checkout") == "T20 D20"
