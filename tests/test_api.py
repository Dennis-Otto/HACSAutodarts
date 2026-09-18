"""Device grant and token rotation tests at the HTTP boundary."""

import asyncio
import time
from dataclasses import replace
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.autodarts.api import (
    API_BASE,
    DEVICE_CODE_URL,
    DEVICE_TOKEN_URL,
    REFRESH_URL,
    AutodartsAuthError,
    AutodartsCloudClient,
    AutodartsConnectionError,
    DeviceAuthorization,
    request_device_code,
    wait_for_device_token,
)

CLIENT_ID = "registered-test-client"
TOKEN = {
    "access_token": "test-access",
    "refresh_token": "test-refresh",
    "expires_in": 900,
}
DEVICE = {
    "device_code": "private-test-device-code",
    "user_code": "ABCD-EFGH",
    "verification_uri": "https://auth.autodarts.io/link",
    "verification_uri_complete": "https://auth.autodarts.io/link?user_code=ABCD-EFGH",
    "expires_in": 600,
    "interval": 5,
}


def grant():
    return DeviceAuthorization(
        DEVICE["device_code"],
        DEVICE["user_code"],
        DEVICE["verification_uri"],
        DEVICE["verification_uri_complete"],
        time.monotonic() + 600,
        5,
    )


async def test_device_request(hass, aioclient_mock):
    aioclient_mock.post(DEVICE_CODE_URL, json=DEVICE)
    device = await request_device_code(async_get_clientsession(hass), CLIENT_ID)
    assert device.user_code == "ABCD-EFGH"
    assert device.interval == 5
    assert DEVICE["device_code"] not in repr(device)
    assert aioclient_mock.mock_calls[0][2] == {"client_id": CLIENT_ID}


@pytest.mark.parametrize("code", ["invalid_client", "unauthorized_client"])
async def test_unregistered_client(hass, aioclient_mock, code):
    aioclient_mock.post(DEVICE_CODE_URL, status=400, json={"error": code})
    with pytest.raises(AutodartsAuthError, match=code):
        await request_device_code(async_get_clientsession(hass), CLIENT_ID)


async def test_pending_and_slow_down(hass):
    with (
        patch(
            "custom_components.autodarts.api._auth_request", new_callable=AsyncMock
        ) as request,
        patch(
            "custom_components.autodarts.api.asyncio.sleep", new_callable=AsyncMock
        ) as sleep,
    ):
        request.side_effect = [
            AutodartsAuthError("authorization_pending"),
            AutodartsAuthError("slow_down"),
            TOKEN,
        ]
        token = await wait_for_device_token(
            async_get_clientsession(hass), CLIENT_ID, grant()
        )
    assert [c.args[0] for c in sleep.call_args_list] == [5, 5, 10]
    assert token["refresh_token"] == TOKEN["refresh_token"]
    assert request.call_args.args[1] == DEVICE_TOKEN_URL
    assert (
        request.call_args.args[2]["grant_type"]
        == "urn:ietf:params:oauth:grant-type:device_code"
    )
    assert request.call_args.args[2]["device_code"] == DEVICE["device_code"]


@pytest.mark.parametrize("code", ["access_denied", "expired_token", "invalid_client"])
async def test_terminal_device_errors(hass, code):
    with (
        patch(
            "custom_components.autodarts.api._auth_request",
            side_effect=AutodartsAuthError(code),
        ) as request,
        patch("custom_components.autodarts.api.asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(AutodartsAuthError, match=code):
            await wait_for_device_token(
                async_get_clientsession(hass), CLIENT_ID, grant()
            )
    assert request.call_count == 1


async def test_expired_code_never_polled(hass):
    with patch("custom_components.autodarts.api._auth_request") as request:
        with pytest.raises(AutodartsAuthError, match="expired_token"):
            await wait_for_device_token(
                async_get_clientsession(hass),
                CLIENT_ID,
                replace(grant(), expires_at=time.monotonic() - 1),
            )
    request.assert_not_called()


async def test_outage_backs_off_and_recovers(hass):
    with (
        patch(
            "custom_components.autodarts.api._auth_request",
            side_effect=[AutodartsConnectionError(), TOKEN],
        ),
        patch(
            "custom_components.autodarts.api.asyncio.sleep", new_callable=AsyncMock
        ) as sleep,
    ):
        await wait_for_device_token(async_get_clientsession(hass), CLIENT_ID, grant())
    assert [c.args[0] for c in sleep.call_args_list] == [5, 10]


async def test_cancellation_stops_polling(hass):
    with patch("custom_components.autodarts.api._auth_request") as request:
        task = asyncio.create_task(
            wait_for_device_token(async_get_clientsession(hass), CLIENT_ID, grant())
        )
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    request.assert_not_called()


async def test_refresh_persisted_even_when_following_request_fails(
    hass, aioclient_mock
):
    aioclient_mock.post(REFRESH_URL, json=TOKEN)
    aioclient_mock.get(f"{API_BASE}/bs/v0/boards/board-1", status=503)
    persisted = Mock()
    cloud = AutodartsCloudClient(
        async_get_clientsession(hass),
        {
            "access_token": "old-access",
            "refresh_token": "old-refresh",
            "expires_at": 0,
        },
        CLIENT_ID,
        persisted,
    )
    with pytest.raises(AutodartsConnectionError):
        await cloud.get_board("board-1")
    assert persisted.call_args.args[0]["refresh_token"] == "test-refresh"
    assert aioclient_mock.mock_calls[0][2] == {
        "client_id": CLIENT_ID,
        "refresh_token": "old-refresh",
    }
    assert aioclient_mock.mock_calls[1][3] == {"Authorization": "Bearer test-access"}


async def test_concurrent_refresh_only_consumes_token_once(hass, aioclient_mock):
    aioclient_mock.post(REFRESH_URL, json=TOKEN)
    aioclient_mock.get(f"{API_BASE}/bs/v0/boards/board-1", json={"id": "board-1"})
    cloud = AutodartsCloudClient(
        async_get_clientsession(hass),
        {
            "access_token": "old",
            "refresh_token": "old-refresh",
            "expires_at": 0,
        },
        CLIENT_ID,
    )
    await asyncio.gather(cloud.get_board("board-1"), cloud.get_board("board-1"))
    assert sum(str(call[1]) == REFRESH_URL for call in aioclient_mock.mock_calls) == 1


async def test_rejected_access_token_is_refreshed_once(hass):
    def response(status):
        result = Mock()
        result.status = status
        result.json = AsyncMock(return_value={"id": "board-1"})
        context = AsyncMock()
        context.__aenter__.return_value = result
        return context

    session = Mock(spec=aiohttp.ClientSession)
    session.get.side_effect = [response(401), response(200)]
    cloud = AutodartsCloudClient(
        session,
        {
            "access_token": "old",
            "refresh_token": "old-refresh",
            "expires_at": time.time() + 900,
        },
        CLIENT_ID,
    )
    with patch(
        "custom_components.autodarts.api._auth_request", return_value=TOKEN
    ) as refresh:
        assert await cloud.get_board("board-1") == {"id": "board-1"}
    refresh.assert_awaited_once()
    assert session.get.call_count == 2


async def test_repeated_401_requires_reauth(hass, aioclient_mock):
    aioclient_mock.post(REFRESH_URL, json=TOKEN)
    aioclient_mock.get(f"{API_BASE}/bs/v0/boards/board-1", status=401)
    cloud = AutodartsCloudClient(
        async_get_clientsession(hass),
        {
            "access_token": "old",
            "refresh_token": "old-refresh",
            "expires_at": time.time() + 900,
        },
        CLIENT_ID,
    )
    with pytest.raises(AutodartsAuthError, match="invalid_token"):
        await cloud.get_board("board-1")
    assert aioclient_mock.call_count == 3


@pytest.mark.parametrize(
    "body", [{}, [], {**DEVICE, "interval": 0}, {**DEVICE, "expires_in": -1}]
)
async def test_malformed_device_response(hass, aioclient_mock, body):
    aioclient_mock.post(DEVICE_CODE_URL, json=body)
    with pytest.raises(AutodartsConnectionError):
        await request_device_code(async_get_clientsession(hass), CLIENT_ID)


@pytest.mark.parametrize(
    "status,body,error",
    [
        (400, {"error": "invalid_grant"}, AutodartsAuthError),
        (503, {}, AutodartsConnectionError),
        (200, {"access_token": "incomplete"}, AutodartsConnectionError),
    ],
)
async def test_refresh_failure(hass, aioclient_mock, status, body, error):
    aioclient_mock.post(REFRESH_URL, status=status, json=body)
    cloud = AutodartsCloudClient(
        async_get_clientsession(hass),
        {
            "access_token": "old",
            "refresh_token": "old-refresh",
            "expires_at": 0,
        },
        CLIENT_ID,
    )
    with pytest.raises(error):
        await cloud.get_board("board-1")
    assert cloud.token["refresh_token"] == "old-refresh"
