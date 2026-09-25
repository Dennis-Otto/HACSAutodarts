"""Local Board Manager API. Configuration secrets never leave this client."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import aiohttp
from yarl import URL

from .errors import AutodartsApiError, AutodartsConnectionError

CONFIG_SWITCHES = ("auto_calibrate_on_start", "auto_calibrate", "auto_distortion")
STANDBY_MINUTES = (5, 10, 15, 30, 60)
COMMANDS = {
    "start": ("PUT", "/api/start"),
    "stop": ("PUT", "/api/stop"),
    "reset": ("POST", "/api/reset"),
    "restart": ("POST", "/api/restart"),
    "calibrate": ("POST", "/api/config/calibration/auto"),
    "connect": ("PUT", "/api/upstream/connect"),
    "disconnect": ("PUT", "/api/upstream/disconnect"),
    "start_streams": ("PUT", "/api/streams/start"),
    "stop_streams": ("PUT", "/api/streams/stop"),
}


class AutodartsLocalCommandError(AutodartsApiError):
    """The board rejected an action; do not retry a possibly executed command."""


class AutodartsEndpointMissing(AutodartsLocalCommandError):
    """This firmware does not implement the requested route."""


class AutodartsLocalClient:
    """Control one local board, using the Board Manager's own HTTP protocol."""

    def __init__(self, host: str, port: int, session: aiohttp.ClientSession) -> None:
        self._session = session
        self.base_url = str(URL.build(scheme="http", host=host, port=port))
        self._command_lock = asyncio.Lock()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict | None = None,
        response_type: str = "json",
        timeout: int = 10,
    ) -> Any:
        try:
            async with asyncio.timeout(timeout):
                kwargs = {"json": payload} if payload is not None else {}
                async with self._session.request(
                    method, f"{self.base_url}{path}", **kwargs
                ) as response:
                    if response.status in (404, 405):
                        raise AutodartsEndpointMissing(
                            "Endpoint not supported by this board"
                        )
                    if response.status >= 400 and method != "GET":
                        raise AutodartsLocalCommandError(
                            f"Board rejected command (HTTP {response.status})"
                        )
                    response.raise_for_status()
                    if response_type == "none":
                        # PATCH /config may return secrets. Discard the response.
                        await response.read()
                        return None
                    if response_type == "text":
                        return (await response.text()).strip()
                    if response_type == "image":
                        if not response.headers.get("Content-Type", "").startswith(
                            "image/"
                        ):
                            raise AutodartsConnectionError("No camera image available")
                        return await response.read()
                    return await response.json()
        except (TimeoutError, aiohttp.ClientError, ValueError) as err:
            # Never log response bodies, which can include the board API key.
            raise AutodartsConnectionError(
                "Unable to communicate with local board"
            ) from err

    async def get_state(self) -> dict[str, Any]:
        state = await self._request("GET", "/api/state")
        if not isinstance(state, dict) or not isinstance(state.get("running"), bool):
            raise AutodartsConnectionError("Invalid Board Manager state")
        return state

    async def get_config(self) -> dict[str, Any]:
        """Return only identity and supported controls, never auth/camera secrets."""
        raw = await self._request("GET", "/api/config")
        if not isinstance(raw, dict):
            raise AutodartsConnectionError("Invalid Board Manager configuration")
        auth, cam, motion = (raw.get(key) or {} for key in ("auth", "cam", "motion"))
        if not all(isinstance(section, dict) for section in (auth, cam, motion)):
            raise AutodartsConnectionError("Invalid Board Manager configuration")
        result = {
            key: cam[key] for key in CONFIG_SWITCHES if isinstance(cam.get(key), bool)
        }
        if isinstance(auth.get("board_id"), str):
            result["board_id"] = auth["board_id"]
        if isinstance(cam.get("cams"), list):
            result["camera_count"] = len(cam["cams"])
        if motion.get("standby_minutes") in STANDBY_MINUTES:
            result["standby_minutes"] = motion["standby_minutes"]
        return result

    async def get_version(self) -> str:
        return await self._request("GET", "/api/version", response_type="text")

    async def get_stats(self) -> dict[str, Any]:
        result = await self._request("GET", "/api/state/stats")
        if not isinstance(result, dict):
            raise AutodartsConnectionError("Invalid detection statistics")
        return result

    async def get_camera_stats(self) -> dict[str, Any]:
        result = await self._request("GET", "/api/cams/stats")
        if not isinstance(result, dict):
            raise AutodartsConnectionError("Invalid camera statistics")
        return result

    async def get_motion_state(self) -> dict[str, Any]:
        result = await self._request("GET", "/api/state/motion")
        if not isinstance(result, dict):
            raise AutodartsConnectionError("Invalid motion state")
        return result

    async def get_camera_state(self) -> dict[str, Any]:
        result = await self._request("GET", "/api/cams/state")
        if not isinstance(result, dict):
            raise AutodartsConnectionError("Invalid camera state")
        return result

    async def events(self) -> AsyncIterator[tuple[str, dict]]:
        """Receive local notifications; no subscription or control writes needed."""
        try:
            async with asyncio.timeout(10):
                socket = await self._session.ws_connect(
                    f"{self.base_url}/api/events",
                    heartbeat=30,
                    timeout=aiohttp.ClientWSTimeout(ws_close=5),
                    max_msg_size=1024 * 1024,
                )
            async with socket:
                yield "connected", {}
                async for message in socket:
                    if message.type == aiohttp.WSMsgType.ERROR:
                        raise AutodartsConnectionError("Local event connection failed")
                    if message.type != aiohttp.WSMsgType.TEXT:
                        continue
                    try:
                        envelope = message.json()
                    except (ValueError, TypeError):
                        continue
                    if not isinstance(envelope, dict):
                        continue
                    kind, data = envelope.get("type"), envelope.get("data")
                    if kind in (
                        "state",
                        "motion_state",
                        "cam_state",
                        "stats",
                        "cam_stats",
                    ) and isinstance(data, dict):
                        yield kind, data
        except (aiohttp.ClientError, TimeoutError) as err:
            raise AutodartsConnectionError(
                "Local event connection unavailable"
            ) from err

    async def calibrate_camera(self, index: int) -> None:
        if type(index) is not int or index < 0:
            raise ValueError("Invalid camera index")
        async with self._command_lock:
            await self._request(
                "POST",
                f"/api/config/calibration/auto/{index}?distortion=true",
                response_type="none",
                timeout=60,
            )

    async def get_camera_image(self, index: int) -> bytes:
        return await self._request(
            "GET", f"/api/img/cams/{index}", response_type="image"
        )

    async def command(self, command: str) -> None:
        """Send an explicit user action once. Only missing routes permit fallback."""
        method, path = COMMANDS[command]
        async with self._command_lock:
            try:
                await self._request(
                    method,
                    path,
                    response_type="none",
                    timeout=60 if command == "calibrate" else 10,
                )
            except AutodartsEndpointMissing:
                if command not in ("start", "stop"):
                    raise
                await self._request(
                    method, f"/api/detection/{command}", response_type="none"
                )

    async def set_config_switch(self, key: str, enabled: bool) -> None:
        if key not in CONFIG_SWITCHES or not isinstance(enabled, bool):
            raise ValueError("Unsupported board setting")
        async with self._command_lock:
            await self._request(
                "PATCH",
                "/api/config",
                payload={"cam": {key: enabled}},
                response_type="none",
            )

    async def set_standby_minutes(self, minutes: int) -> None:
        if minutes not in STANDBY_MINUTES:
            raise ValueError("Unsupported standby duration")
        async with self._command_lock:
            await self._request(
                "PATCH",
                "/api/config",
                payload={"motion": {"standby_minutes": minutes}},
                response_type="none",
            )

    async def test_connection(self) -> bool:
        try:
            await self.get_state()
        except AutodartsApiError:
            return False
        return True
