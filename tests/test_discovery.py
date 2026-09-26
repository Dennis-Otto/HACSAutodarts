"""Finding boards: mDNS announcements, the Autodarts lookup and manual fallback."""

from ipaddress import ip_address

from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    SOURCE_ZEROCONF,
)
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.autodarts.const import DISCOVERY_URL

from .local_helpers import BASE, local_entry_data, mock_board, mock_board_v2

OTHER = "http://192.0.2.20:3180"
LISTED = [
    {
        "boardId": "board-1",
        "name": "Living room",
        "ip": "192.0.2.10",
        "port": "3180",
        "insecurePort": "3180",
        "version": "2.0.0",
    },
    {"boardId": "", "ip": "192.0.2.30"},
    {"boardId": "no-ip"},
    {"boardId": "bad-ip", "ip": "not an address"},
    "garbage",
]


def zeroconf(host: str = "192.0.2.10", properties: dict | None = None):
    return ZeroconfServiceInfo(
        ip_address=ip_address(host),
        ip_addresses=[ip_address(host)],
        hostname="autodarts.local.",
        name="autodarts-board._autodarts-board._tcp.local.",
        port=3180,
        type="_autodarts-board._tcp.local.",
        properties={"id": "25648ad55ac6060d", "cams": "3"}
        if properties is None
        else properties,
    )


async def start(hass, source=SOURCE_USER, entry=None):
    context = {"source": source}
    if entry:
        context["entry_id"] = entry.entry_id
    return await hass.config_entries.flow.async_init("autodarts", context=context)


async def test_announced_board_is_added_with_one_click(hass, aioclient_mock):
    mock_board_v2(aioclient_mock)
    result = await hass.config_entries.flow.async_init(
        "autodarts", context={"source": SOURCE_ZEROCONF}, data=zeroconf()
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"
    assert result["description_placeholders"] == {
        "host": "192.0.2.10",
        "version": "2.0.0",
        "cameras": "3",
    }
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {**local_entry_data(), "api_generation": 2}
    assert result["result"].unique_id == "board-1"


async def test_announced_address_property_is_preferred(hass, aioclient_mock):
    mock_board_v2(aioclient_mock)
    info = zeroconf("fe80::1", {"ip": "192.0.2.10", "cams": "3"})
    result = await hass.config_entries.flow.async_init(
        "autodarts", context={"source": SOURCE_ZEROCONF}, data=info
    )
    assert result["description_placeholders"]["host"] == "192.0.2.10"


async def test_announced_known_board_updates_its_address(hass, aioclient_mock):
    aioclient_mock.get(OTHER + "/api/state", json={"running": False})
    aioclient_mock.get(
        OTHER + "/api/config", json={"auth": {"board_id": "board-1"}, "cam": {}}
    )
    aioclient_mock.get(OTHER + "/api/version", text="2.0.0")
    entry = MockConfigEntry(
        domain="autodarts", version=2, unique_id="board-1", data=local_entry_data()
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        "autodarts", context={"source": SOURCE_ZEROCONF}, data=zeroconf("192.0.2.20")
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "192.0.2.20"


async def test_announced_board_that_does_not_answer_is_ignored(hass, aioclient_mock):
    aioclient_mock.get(BASE + "/api/state", status=503)
    result = await hass.config_entries.flow.async_init(
        "autodarts", context={"source": SOURCE_ZEROCONF}, data=zeroconf()
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "cannot_connect_local"


async def test_announced_board_without_board_id_asks_for_setup(hass, aioclient_mock):
    mock_board(aioclient_mock, config={"auth": {}, "cam": {}, "motion": {}})
    result = await hass.config_entries.flow.async_init(
        "autodarts", context={"source": SOURCE_ZEROCONF}, data=zeroconf()
    )
    assert result["reason"] == "board_not_configured"


async def test_search_lists_new_boards_and_connects_locally(hass, aioclient_mock):
    aioclient_mock.get(DISCOVERY_URL, json=LISTED)
    mock_board_v2(aioclient_mock)
    result = await start(hass)
    assert result["menu_options"] == ["discover", "local"]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discover"}
    )
    assert result["step_id"] == "discover"
    options = result["data_schema"].schema["board_id"].container
    assert options == {"board-1": "Living room · 192.0.2.10 · 2.0.0"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"board_id": "board-1"}
    )
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {**local_entry_data(), "api_generation": 2}


async def test_search_without_new_boards_falls_back_to_address(hass, aioclient_mock):
    aioclient_mock.get(DISCOVERY_URL, json=LISTED)
    MockConfigEntry(domain="autodarts", unique_id="board-1").add_to_hass(hass)
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discover"}
    )
    assert result["step_id"] == "local"
    assert result["errors"] == {"base": "no_boards_found"}


async def test_unavailable_search_falls_back_to_address(hass, aioclient_mock):
    aioclient_mock.get(DISCOVERY_URL, status=503)
    result = await start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discover"}
    )
    assert result["step_id"] == "local"
    assert result["errors"] == {"base": "discovery_failed"}


async def test_reconfigure_by_search_updates_the_address(hass, aioclient_mock):
    listed = [{**LISTED[0], "ip": "192.0.2.20"}]
    aioclient_mock.get(DISCOVERY_URL, json=listed)
    aioclient_mock.get(OTHER + "/api/state", json={"running": False})
    aioclient_mock.get(
        OTHER + "/api/config", json={"auth": {"board_id": "board-1"}, "cam": {}}
    )
    aioclient_mock.get(OTHER + "/api/version", text="2.0.0")
    mock_board_v2(aioclient_mock)
    entry = MockConfigEntry(
        domain="autodarts", version=2, unique_id="board-1", data=local_entry_data()
    )
    entry.add_to_hass(hass)
    result = await start(hass, SOURCE_RECONFIGURE, entry)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discover"}
    )
    # The configured board is still offered when reconfiguring it.
    assert result["step_id"] == "discover"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"board_id": "board-1"}
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["host"] == "192.0.2.20"
