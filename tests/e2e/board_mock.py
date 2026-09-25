"""Deterministic Board Manager 1.0.7 double for the Docker end-to-end test.

Serves the local HTTP and WebSocket protocol used by the integration, records every
write command and rejects routes the integration is not expected to call.
"""

from __future__ import annotations

import copy

from aiohttp import WSMsgType, web

BOARD_ID = "e2e-board"
# Synthetic secret: it must never reach Home Assistant state, diagnostics or logs.
API_KEY = "e2e-only-board-api-key"
PORT = 3180

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
        for socket in list(self.sockets):
            await socket.send_json({"type": "state", "data": self.state})


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
        return web.Response(text="1.0.7\n")

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

    @api.get("/api/events")
    async def events(request):
        socket = web.WebSocketResponse()
        await socket.prepare(request)
        board.sockets.add(socket)
        try:
            async for message in socket:
                if message.type == WSMsgType.ERROR:
                    break
        finally:
            board.sockets.discard(socket)
        return socket

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


if __name__ == "__main__":
    web.run_app(create_app(), port=PORT, print=None)
