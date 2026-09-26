"""Board Manager 2: one system read, its own entities and generation changes."""

from copy import deepcopy

from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.autodarts.diagnostics import async_get_config_entry_diagnostics
from custom_components.autodarts.local_api import board_generation

from .local_helpers import (
    BASE,
    STATE,
    SYSTEM,
    local_entry_data,
    mock_board,
    mock_board_v2,
)
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


async def test_board_pc_details_without_private_names(hass, aioclient_mock):
    entry = await setup_v2(hass, aioclient_mock)
    system = hass.states.get(entity_id(hass, "sensor", "host_os"))
    assert system.state == "Debian 13"
    assert system.attributes["kernel"] == "6.12.107+deb13-amd64"
    assert system.attributes["architecture"] == "x86_64"
    processor = hass.states.get(entity_id(hass, "sensor", "host_processor"))
    assert processor.state == "Intel(R) Core(TM) i3-9100T CPU @ 3.10GHz"
    assert processor.attributes["cores"] == 4
    vision = hass.states.get(entity_id(hass, "sensor", "vision_version"))
    assert vision.state == "2.0.0"
    assert vision.attributes["opencv_version"] == "5.0.0"
    registry = er.async_get(hass)
    for key in ("host_os", "host_processor", "vision_version"):
        entry_ = registry.async_get(entity_id(hass, "sensor", key))
        assert entry_.entity_category == er.EntityCategory.DIAGNOSTIC
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["local"]["board_pc"]["vision_version"] == "2.0.0"
    for private in ("dartboard-pc", "198.51.100.7", "USB Camera"):
        assert private not in str(entry.runtime_data.local.data)
        assert private not in str(diagnostics)
        assert private not in str(hass.states.async_all())


async def test_board_without_host_details_keeps_working(hass, aioclient_mock):
    aioclient_mock.get(BASE + "/api/host", status=404)
    entry = await setup_v2(hass, aioclient_mock)
    assert entry.runtime_data.local.data["board_pc"] == {}
    assert state(hass, "sensor", "host_os") == "unknown"
    assert state(hass, "sensor", "vision_version") == "unknown"
    assert state(hass, "sensor", "cpu_usage") == "12.5"


async def test_failed_host_read_is_asked_again_at_the_next_poll(hass, aioclient_mock):
    aioclient_mock.get(BASE + "/api/host", status=503)
    entry = await setup_v2(hass, aioclient_mock)
    coordinator = entry.runtime_data.local
    assert "board_pc" not in coordinator.data
    assert state(hass, "sensor", "cpu_usage") == "12.5"

    aioclient_mock.clear_requests()
    mock_board_v2(aioclient_mock)
    await coordinator.async_refresh()
    assert state(hass, "sensor", "host_os") == "Debian 13"
    assert [call[1].path for call in aioclient_mock.mock_calls].count("/api/host") == 1


async def test_board_that_tells_no_version_runs_as_classic(hass, aioclient_mock):
    aioclient_mock.get(BASE + "/api/version", status=404)
    entry = await setup_local(hass, aioclient_mock)
    assert "api_generation" not in entry.data
    assert entry.runtime_data.local.generation is None
    ids = unique_ids(hass, entry)
    assert "board-1_upstream" in ids and "board-1_cloud_link" not in ids
    assert state(hass, "switch", "detection") == "off"


async def test_cameras_are_read_right_after_the_detection_starts(hass, aioclient_mock):
    """Board Manager 2 sends no camera messages, so a start triggers one read."""
    stopped = deepcopy(SYSTEM)
    stopped["camState"] = {"isOpened": False, "isRunning": False}
    entry = await setup_v2(hass, aioclient_mock, system=stopped)
    coordinator = entry.runtime_data.local
    assert state(hass, "binary_sensor", "cameras_active") == "off"

    aioclient_mock.clear_requests()
    mock_board_v2(aioclient_mock, state={**STATE, "running": True, "status": "Throw"})
    board = {**STATE, "running": True, "status": "Starting", "event": "Starting"}
    coordinator.async_receive("state", board)
    await hass.async_block_till_done()
    assert state(hass, "binary_sensor", "cameras_active") == "on"
    reads = [call[1].path for call in aioclient_mock.mock_calls]
    assert reads.count("/api/system") == 1

    # Takeouts change the status too, but never the cameras.
    aioclient_mock.clear_requests()
    mock_board_v2(aioclient_mock, state={**STATE, "running": True, "status": "Throw"})
    for status in ("Throw", "Takeout in progress", "Throw"):
        coordinator.async_receive("state", {**board, "status": status})
    await hass.async_block_till_done()
    assert not aioclient_mock.mock_calls
