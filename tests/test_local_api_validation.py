"""Reject malformed Board Manager answers instead of passing them to entities."""

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.autodarts.errors import AutodartsConnectionError
from custom_components.autodarts.local_api import (
    AutodartsEndpointMissing,
    AutodartsLocalClient,
)

from .local_helpers import BASE, CONFIG, STATE


@pytest.fixture
async def client(hass, aioclient_mock):
    return AutodartsLocalClient("192.0.2.10", 3180, async_get_clientsession(hass))


@pytest.mark.parametrize(
    "path,read",
    [
        ("/api/config", "get_config"),
        ("/api/system", "get_system"),
        ("/api/state/stats", "get_stats"),
        ("/api/cams/stats", "get_camera_stats"),
        ("/api/state/motion", "get_motion_state"),
        ("/api/cams/state", "get_camera_state"),
    ],
)
async def test_non_object_answers_are_rejected(client, aioclient_mock, path, read):
    aioclient_mock.get(f"{BASE}{path}", json=["not", "an", "object"])
    with pytest.raises(AutodartsConnectionError):
        await getattr(client, read)()


@pytest.mark.parametrize("section", ["auth", "cam", "motion"])
async def test_malformed_config_sections_are_rejected(client, aioclient_mock, section):
    aioclient_mock.get(f"{BASE}/api/config", json={**CONFIG, section: "broken"})
    with pytest.raises(AutodartsConnectionError):
        await client.get_config()


async def test_identify_works_without_a_version_route(client, aioclient_mock):
    aioclient_mock.get(f"{BASE}/api/state", json=STATE)
    aioclient_mock.get(f"{BASE}/api/config", json=CONFIG)
    aioclient_mock.get(f"{BASE}/api/version", status=404)
    assert await client.identify() == {
        "board_id": "board-1",
        "version": None,
        "camera_count": 3,
    }


async def test_missing_route_is_only_retried_for_start_and_stop(client, aioclient_mock):
    aioclient_mock.post(f"{BASE}/api/reset", status=404)
    with pytest.raises(AutodartsEndpointMissing):
        await client.command("reset")
    assert len(aioclient_mock.mock_calls) == 1


async def test_invalid_camera_index_sends_nothing(client, aioclient_mock):
    for index in (-1, 1.5, "1", True):
        with pytest.raises(ValueError):
            await client.calibrate_camera(index)
    assert not aioclient_mock.mock_calls


async def test_connection_check(client, aioclient_mock):
    aioclient_mock.get(f"{BASE}/api/state", json=STATE)
    assert await client.test_connection() is True
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE}/api/state", status=500)
    assert await client.test_connection() is False
