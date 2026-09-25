"""Board Manager 2: one system read, its own entities and generation changes."""

from copy import deepcopy

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.autodarts.diagnostics import async_get_config_entry_diagnostics
from custom_components.autodarts.local_api import board_generation

from .local_helpers import BASE, SYSTEM, local_entry_data, mock_board, mock_board_v2
from .test_local_setup import entity_id, setup_local, state

SECRETS = ("private-board-api-key", "private-tls-key")


def unique_ids(hass, entry) -> set[str]:
    registry = er.async_get(hass)
    return {
        item.unique_id
        for item in er.async_entries_for_config_entry(registry, entry.entry_id)
    }


async def setup_v2(hass, aioclient_mock, **kwargs):
    mock_board_v2(aioclient_mock, **kwargs)
    entry = MockConfigEntry(domain="autodarts", version=2, data=local_entry_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_board_manager_2_entities_and_one_system_read(hass, aioclient_mock):
    entry = await setup_v2(hass, aioclient_mock)
    assert entry.data["api_generation"] == 2
    ids = unique_ids(hass, entry)
    assert {"board-1_cloud_link", "board-1_cpu_usage", "board-1_board_software"} <= ids
    assert not {"board-1_upstream", "board-1_connect", "board-1_disconnect"} & ids
    assert state(hass, "binary_sensor", "cloud_link") == "on"
    assert state(hass, "sensor", "cpu_usage") == "12.5"
    update = hass.states.get(entity_id(hass, "update", "board_software"))
    assert update.state == "on"
    assert update.attributes["installed_version"] == "2.0.0"
    assert update.attributes["latest_version"] == "2.0.2"
    assert state(hass, "binary_sensor", "cameras_active") == "on"
    assert state(hass, "switch", "auto_calibrate") == "on"
    registry = er.async_get(hass)
    memory = registry.async_get(entity_id(hass, "sensor", "memory_usage"))
    assert memory.disabled_by == er.RegistryEntryDisabler.INTEGRATION

    aioclient_mock.clear_requests()
    mock_board_v2(aioclient_mock)
    await entry.runtime_data.local.async_refresh()
    paths = {call[1].path for call in aioclient_mock.mock_calls}
    assert paths == {"/api/state", "/api/system"}


async def test_board_manager_2_secrets_never_leave_the_client(hass, aioclient_mock):
    entry = await setup_v2(hass, aioclient_mock)
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["board_manager_generation"] == 2
    for secret in SECRETS:
        assert secret not in str(entry.runtime_data.local.data)
        assert secret not in str(diagnostics)
        assert secret not in str(hass.states.async_all())


async def test_no_update_means_latest_is_installed(hass, aioclient_mock):
    system = {**deepcopy(SYSTEM), "updateAvailable": ""}
    await setup_v2(hass, aioclient_mock, system=system)
    assert state(hass, "update", "board_software") == "off"


async def test_failed_system_read_keeps_values(hass, aioclient_mock):
    entry = await setup_v2(hass, aioclient_mock)
    aioclient_mock.clear_requests()
    mock_board(aioclient_mock, version="2.0.0")
    aioclient_mock.get(BASE + "/api/system", status=503)
    await entry.runtime_data.local.async_refresh()
    assert state(hass, "sensor", "cpu_usage") == "12.5"
    assert state(hass, "switch", "auto_calibrate") == "on"
    assert state(hass, "binary_sensor", "cloud_link") == "on"


async def test_upgrade_to_board_manager_2_rebuilds_entities(hass, aioclient_mock):
    entry = await setup_local(hass, aioclient_mock)
    assert entry.data["api_generation"] == 1
    assert "board-1_upstream" in unique_ids(hass, entry)
    aioclient_mock.clear_requests()
    mock_board_v2(aioclient_mock)
    coordinator = entry.runtime_data.local
    coordinator._metadata_updated = 0
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert entry.data["api_generation"] == 2
    ids = unique_ids(hass, entry)
    assert "board-1_upstream" not in ids
    assert "board-1_cloud_link" in ids
    assert state(hass, "binary_sensor", "cloud_link") == "on"


async def test_board_without_system_endpoint_returns_to_classic(hass, aioclient_mock):
    mock_board(aioclient_mock)
    aioclient_mock.get(BASE + "/api/system", status=404)
    data = {**local_entry_data(), "api_generation": 2}
    entry = MockConfigEntry(domain="autodarts", version=2, data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.data["api_generation"] == 1
    ids = unique_ids(hass, entry)
    assert "board-1_upstream" in ids
    assert not {"board-1_cloud_link", "board-1_board_software"} & ids


def test_board_generation_from_version():
    assert board_generation("2.0.0") == 2
    assert board_generation("v1.0.7") == 1
    assert board_generation(" 10.1 ") == 10
    for value in (None, "", "beta", "0.9", 2):
        assert board_generation(value) is None
