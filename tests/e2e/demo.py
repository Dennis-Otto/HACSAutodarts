"""Prepare the demo instance: a configured board, a dashboard and a visit in progress.

Runs inside the Home Assistant container like scenario.py and reuses its API helpers.
The resulting instance is used for previews and documentation screenshots.
"""

from __future__ import annotations

import asyncio

import aiohttp
from board_mock import GENERATION, PORT
from scenario import Scenario

DASHBOARD = "autodarts-demo"
STRATEGY_DASHBOARD = "autodarts-auto"


def dart(name: str, number: int, multiplier: int, bed: str, x: float, y: float):
    return {
        "segment": {
            "name": name,
            "number": number,
            "multiplier": multiplier,
            "bed": bed,
        },
        "coords": {"x": x, "y": y},
    }


T20 = dart("T20", 20, 3, "Triple", 0.035, 0.608)
T20_LEFT = dart("T20", 20, 3, "Triple", -0.041, 0.604)
S20 = dart("S20", 20, 1, "SingleOuter", 0.02, 0.8)
S1 = dart("S1", 1, 1, "SingleOuter", 0.2, 0.74)
S5 = dart("S5", 5, 1, "SingleOuter", -0.24, 0.76)
T19 = dart("T19", 19, 3, "Triple", -0.19, -0.575)
D16 = dart("D16", 16, 2, "Double", -0.58, -0.8)
BULL = dart("Bull", 25, 2, "Double", 0.012, -0.02)
OUTER_BULL = dart("25", 25, 1, "Single", -0.06, 0.07)

# Completed visits give the session statistics realistic values.
HISTORY = [
    [T20, S20, S1],
    [T20, T20_LEFT, S5],
    [S20, OUTER_BULL, T19],
    [T20, S20, D16],
    [BULL, S20, S20],
]
CURRENT = [T20, S5, BULL]
# Earlier, finished sessions for the training card's list of past sessions.
EARLIER = [
    [[T20, T20_LEFT, S20], [S20, S1, S5]],
    [[T19, S20, S20], [BULL, OUTER_BULL, S20], [T20, S5, S1]],
]

CARDS = {
    "board": [{"type": "custom:autodarts-card", "grid_options": {"columns": "full"}}],
    "training": [
        {"type": "custom:autodarts-training-card", "grid_options": {"columns": "full"}}
    ],
    "status": [
        {"type": "custom:autodarts-status-card", "grid_options": {"columns": "full"}}
    ],
    "scoreboard": [{"type": "custom:autodarts-scoreboard-card", "caller": True}],
    "players": [{"type": "custom:autodarts-players-card"}],
    "doubles": [{"type": "custom:autodarts-doubles-card"}],
    "styles": [
        {
            "type": "custom:autodarts-card",
            "board_style": "autodarts",
            "layout": "vertical",
        },
        {"type": "custom:autodarts-card", "layout": "board", "title": "Board"},
    ],
}


def dashboard() -> dict:
    wide = {
        "board": 2,
        "training": 2,
        "status": 2,
        "scoreboard": 2,
        "players": 2,
        "doubles": 2,
        "styles": 1,
    }
    return {
        "title": "Autodarts",
        "views": [
            {
                "title": name.title(),
                "path": name,
                "type": "sections",
                "max_columns": 2,
                "sections": [
                    {"type": "grid", "column_span": wide[name], "cards": [card]}
                    for card in cards
                ],
            }
            for name, cards in CARDS.items()
        ],
    }


async def throw(demo: Scenario, darts: list[dict]) -> None:
    for count in range(1, len(darts) + 1):
        await demo.board("POST", "/control/state", json={"throws": darts[:count]})
        await asyncio.sleep(0.4)


async def play(demo: Scenario, visits: list[list[dict]]) -> None:
    """Throw each visit and pull the darts, as a player does."""
    for visit in visits:
        await throw(demo, visit)
        await demo.board(
            "POST",
            "/control/state",
            json={"status": "Takeout in progress", "event": "Takeout started"},
        )
        await demo.board(
            "POST",
            "/control/state",
            json={"status": "Throw", "event": "Takeout finished", "throws": []},
        )
        await asyncio.sleep(0.4)


async def main() -> None:
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        demo = Scenario(session)
        await demo.onboard()
        await demo.connect()
        if GENERATION >= 2:
            result = await demo.discovered_setup()
        else:
            result = await demo.local_flow("board-mock", PORT)
        entry_id = result["result"]["entry_id"]
        await demo.registries(entry_id)
        # A daily goal the demo darts reach halfway, for the training card.
        await demo.service("number", "set_value", "training_daily_goal", value=120)
        await demo.service("button", "press", "start")
        await demo.expect_states({"detection": "on", "realtime_connected": "on"})
        for session in EARLIER:
            await play(demo, session)
            await demo.service("switch", "turn_off", "training_session")
            await demo.expect_states({"training_session": "off"})
        await demo.service("switch", "turn_on", "training_session")
        await demo.expect_states({"training_session": "on", "training_darts": "0"})
        await play(demo, HISTORY)
        await throw(demo, CURRENT)
        await demo.expect_states({"local_visit_score": "115"})

        await demo.ws(
            "lovelace/dashboards/create",
            url_path=DASHBOARD,
            title="Autodarts",
            icon="mdi:bullseye-arrow",
            show_in_sidebar=True,
            require_admin=False,
            mode="storage",
        )
        await demo.ws("lovelace/config/save", url_path=DASHBOARD, config=dashboard())
        # A second dashboard generated entirely by the Autodarts strategy.
        await demo.ws(
            "lovelace/dashboards/create",
            url_path=STRATEGY_DASHBOARD,
            title="Autodarts (automatic)",
            icon="mdi:bullseye",
            show_in_sidebar=True,
            require_admin=False,
            mode="storage",
        )
        await demo.ws(
            "lovelace/config/save",
            url_path=STRATEGY_DASHBOARD,
            config={"strategy": {"type": "custom:autodarts"}},
        )
        await demo.socket.close()


if __name__ == "__main__":
    asyncio.run(main())
