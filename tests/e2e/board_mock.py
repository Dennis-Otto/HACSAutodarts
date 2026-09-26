"""Deterministic Board Manager double for the Docker end-to-end test.

Serves the local HTTP and WebSocket protocol used by the integration, records every
write command and rejects routes the integration is not expected to call.
BOARD_MANAGER=2 switches to the headless Board Manager 2: /api/system, no
upstream routes, and an mDNS announcement like the real board.
"""

from __future__ import annotations

import copy
import os
import socket

from aiohttp import WSMsgType, web

BOARD_ID = "e2e-board"
# Synthetic secret: it must never reach Home Assistant state, diagnostics or logs.
API_KEY = "e2e-only-board-api-key"
TLS_KEY = "e2e-only-tls-key"
PORT = 3180
GENERATION = int(os.environ.get("BOARD_MANAGER", "1"))
VERSION = "2.0.0" if GENERATION >= 2 else "1.0.7"
UPDATE = "2.0.2"
V1_ONLY = {("PUT", "/api/upstream/connect"), ("PUT", "/api/upstream/disconnect")}

COMMANDS = {
    ("PUT", "/api/start"): {"running": True, "status": "Throw", "event": "Started"},
    ("PUT", "/api/stop"): {"running": False, "status": "Stopped", "event": "Stopped"},
    ("POST", "/api/reset"): {"numThrows": 0, "throws": []},
    ("POST", "/api/restart"): {},
    ("POST", "/api/config/calibration/auto"): {},
    ("PUT", "/api/upstream/connect"): {"connected": True},
    ("PUT", "/api/upstream/disconnect"): {"connected": False},
    ("PUT", "/api/streams/start"): {},
    ("PUT", "/api/streams/stop"): {},
}


class Board:
    def __init__(self) -> None:
        self.state = {
            "connected": True,
            "running": False,
            "status": "Stopped",
            "event": "Stopped",
            "numThrows": 0,
            "throws": [],
        }
        self.config = {
            "auth": {"board_id": BOARD_ID, "api_key": API_KEY},
            "cam": {
                "cams": ["/dev/video0", "/dev/video2", "/dev/video4"],
                "width": 1280,
                "height": 1024,
                "fps": 30,
                "auto_calibrate_on_start": True,
                "auto_calibrate": True,
                "auto_distortion": False,
            },
            "motion": {"standby_minutes": 15},
        }
        self.commands: list[dict] = []
        self.unexpected: list[str] = []
        self.sockets: set[web.WebSocketResponse] = set()

    async def record(self, request: web.Request) -> None:
        body = await request.json() if request.can_read_body else None
        self.commands.append(
            {"method": request.method, "path": request.path_qs, "body": body}
        )

    async def publish(self, changes: dict) -> None:
        self.state.update(changes)
        self.state["numThrows"] = len(self.state["throws"])
        for client in list(self.sockets):
            await client.send_json({"type": "state", "data": self.state})


def routes(board: Board) -> web.RouteTableDef:
    api = web.RouteTableDef()

    @api.get("/health")
    async def health(request):
        return web.Response(text="ok")

    @api.get("/api/state")
    async def state(request):
        return web.json_response(board.state)

    @api.get("/api/config")
    async def config(request):
        return web.json_response(board.config)

    @api.patch("/api/config")
    async def patch_config(request):
        await board.record(request)
        for section, values in (await request.json()).items():
            board.config[section].update(values)
        # The real Board Manager echoes its full configuration, including the key.
        return web.json_response(board.config)

    @api.get("/api/version")
    async def version(request):
        return web.Response(text=f"{VERSION}\n")

    @api.get("/api/state/stats")
    async def stats(request):
        return web.json_response({"fps": 12.5 if board.state["running"] else 0.0})

    @api.get("/api/cams/stats")
    async def camera_stats(request):
        fps = 30.0 if board.state["running"] else 0.0
        return web.json_response({"fps": [fps] * len(board.config["cam"]["cams"])})

    @api.get("/api/cams/state")
    async def camera_state(request):
        running = board.state["running"]
        return web.json_response({"isRunning": running, "isOpened": running})

    @api.get("/api/state/motion")
    async def motion(request):
        return web.json_response(
            {
                "isWaiting": False,
                "isStable": True,
                "isDart": False,
                "isHand": False,
                "isTakeoutPartial": False,
                "isTakeoutFull": False,
            }
        )

    @api.post("/api/config/calibration/auto/{index:\\d+}")
    async def calibrate_camera(request):
        await board.record(request)
        return web.json_response({})

    async def system(request):
        running = board.state["running"]
        fps = 30.0 if running else 0.0
        cams = board.config["cam"]["cams"]
        config = copy.deepcopy(board.config)
        config["host"] = {"port": str(PORT), "tls_key": TLS_KEY, "tls_cert": ""}
        return web.json_response(
            {
                "state": {k: board.state[k] for k in ("connected", "event", "running")}
                | {"numThrows": board.state["numThrows"]},
                "config": config,
                "stats": {
                    "cpuPercent": 7.5,
                    "fps": 12.5 if running else 0.0,
                    "memoryBytes": 268435456,
                },
                "camStats": [{"fps": fps, "id": index} for index in range(len(cams))],
                "camState": {"isRunning": running, "isOpened": running},
                "motion": {
                    "isStable": True,
                    "isHand": False,
                    "isTakeoutPartial": False,
                    "isTakeoutFull": False,
                    "camStates": [],
                },
                "link": "connected" if board.state["connected"] else "disconnected",
                "version": VERSION,
                "updateAvailable": UPDATE,
                "calibrated": True,
                "blocker": "none",
            }
        )

    async def host(request):
        # Like the real board PC, including the details the integration drops.
        return web.json_response(
            {
                "os": "linux",
                "platform": "debian",
                "platformVersion": "13",
                "kernelArch": "x86_64",
                "kernelVersion": "6.12.107+deb13-amd64",
                "cpu": {
                    "cores": 4,
                    "mhz": 3400.4,
                    "model": "Intel(R) Core(TM) i3-9100T",
                },
                "visionVersion": VERSION,
                "openCVVersion": "5.0.0",
                "clientVersion": VERSION,
                "hostname": "e2e-dartboard",
                "ip": "192.0.2.99",
                "cam1": {"name": "E2E Camera", "pid": "0001", "vid": "0002"},
            }
        )

    if GENERATION >= 2:
        api.get("/api/system")(system)
        api.get("/api/host")(host)

    @api.get("/api/events")
    async def events(request):
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)
        board.sockets.add(websocket)
        try:
            async for message in websocket:
                if message.type == WSMsgType.ERROR:
                    break
        finally:
            board.sockets.discard(websocket)
        return websocket

    @api.post("/control/state")
    async def control_state(request):
        await board.publish(await request.json())
        return web.json_response(board.state)

    @api.get("/control/requests")
    async def control_requests(request):
        return web.json_response(
            {
                "commands": board.commands,
                "unexpected": board.unexpected,
                "sockets": len(board.sockets),
            }
        )

    return api


def create_app() -> web.Application:
    board = Board()
    app = web.Application()
    app.add_routes(routes(board))

    for (method, path), changes in COMMANDS.items():
        if GENERATION >= 2 and (method, path) in V1_ONLY:
            continue  # Board Manager 2 has no upstream routes.

        async def command(request, changes=changes):
            await board.record(request)
            if changes:
                await board.publish(copy.deepcopy(changes))
            return web.json_response({})

        app.router.add_route(method, path, command)

    async def unexpected(request):
        board.unexpected.append(f"{request.method} {request.path_qs}")
        raise web.HTTPNotFound

    # Registered last, so only routes without a Board Manager double end here.
    app.router.add_route("*", "/{tail:.*}", unexpected)
    return app


async def announce(app: web.Application) -> None:
    """Board Manager 2 announces itself on the LAN like the real board."""
    from zeroconf import ServiceInfo
    from zeroconf.asyncio import AsyncZeroconf

    address = socket.gethostbyname(socket.gethostname())
    zeroconf = AsyncZeroconf(interfaces=[address])
    info = ServiceInfo(
        "_autodarts-board._tcp.local.",
        "autodarts-board._autodarts-board._tcp.local.",
        addresses=[socket.inet_aton(address)],
        port=PORT,
        properties={"id": "e2e0000000000001", "ip": address, "cams": "3"},
        server="autodarts-e2e.local.",
    )
    await zeroconf.async_register_service(info)

    async def withdraw(app: web.Application) -> None:
        await zeroconf.async_unregister_service(info)
        await zeroconf.async_close()

    app.on_cleanup.append(withdraw)


if __name__ == "__main__":
    app = create_app()
    if GENERATION >= 2:
        app.on_startup.append(announce)
    web.run_app(app, port=PORT, print=None)
