"""Verify the dashboard cards in a real browser against the demo instance.

Runs in the Playwright container on the demo's Compose network (see browser.sh).
"""

from __future__ import annotations

import json
import os
import urllib.request

from playwright.sync_api import Browser, Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout

HA = "http://homeassistant:8123"
BOARD = "http://board-mock:3180"
LOADS = 5
# Board Manager generation of the demo board, passed on by browser.sh.
GENERATION = int(os.environ.get("BOARD_MANAGER", "1"))


def find(tag: str) -> str:
    """A page function returning every card element with this tag, in shadow roots too."""
    return f"""
() => {{
  const cards = [];
  (function collect(root) {{
    root.querySelectorAll('{tag}').forEach((card) => cards.push(card));
    root.querySelectorAll('*').forEach((el) => el.shadowRoot && collect(el.shadowRoot));
  }})(document);
  return cards;
}}
"""


CARDS = find("autodarts-card")
TRAINING_CARDS = find("autodarts-training-card")
STATUS_CARDS = find("autodarts-status-card")
RENDERED = f"() => ({CARDS})().filter((card) => card.shadowRoot?.querySelector('.board svg')).length"
CARD_STATE = f"""
() => {{
  const card = ({CARDS})()[0];
  const root = card.shadowRoot;
  return {{
    score: root.querySelector('.score').textContent,
    slots: [...root.querySelectorAll('.slot .segment')].map((el) => el.textContent),
    latest: [...root.querySelectorAll('.slot')].findIndex((el) => el.classList.contains('latest')),
    hits: root.querySelectorAll('.hits .hit').length,
    darts: root.querySelectorAll('.darts .dart').length,
    blinking: root.querySelector('.hits').classList.contains('blink'),
    status: root.querySelector('.pill').textContent,
    toggle: root.querySelector('[data-action="toggle"]').textContent,
    numbers: root.querySelectorAll('.numbers text').length,
    beds: root.querySelectorAll('.face path').length,
    recent: [...root.querySelectorAll('.recent-visit')].map((el) => el.textContent),
  }};
}}
"""
TRAINING_STATE = f"""
() => {{
  const root = ({TRAINING_CARDS})()[0].shadowRoot;
  const text = (selector) => root.querySelector(selector)?.textContent;
  return {{
    average: text('.average'),
    darts: text('[data-total="darts"]'),
    visits: text('[data-total="visits"]'),
    heat: root.querySelectorAll('.heat-layer path').length,
    top: [...root.querySelectorAll('.top-row .key')].map((el) => el.textContent),
    history: root.querySelectorAll('.history-chart .visit-bar:not(.empty)').length,
    highest: root.querySelector('[data-tile="highest"] .value')?.textContent,
    sessions: [...root.querySelectorAll('.session-table tbody tr')].map(
      (row) => [...row.children].slice(2).map((cell) => cell.textContent)
    ),
    session: text('[data-action="session"]'),
    state: text('.session-state'),
  }};
}}
"""
STATUS_STATE = f"""
() => {{
  const root = ({STATUS_CARDS})()[0].shadowRoot;
  return {{
    cameras: root.querySelectorAll('.camera').length,
    version: root.querySelector('.version')?.textContent,
    update: root.querySelector('.update-badge')?.textContent,
    detection: root.querySelector('.toggle')?.getAttribute('aria-checked'),
    chips: root.querySelectorAll('.chip').length,
    system: !root.querySelector('.system-tile')?.hidden,
    info: root.querySelector('.system-info')?.hidden ? '' : root.querySelector('.system-info')?.textContent,
  }};
}}
"""


# Records page errors with their text; Playwright reports some only as "Object".
CAPTURE_ERRORS = r"""
window.__pageErrors = [];
window.addEventListener("error", (event) => {
  window.__pageErrors.push(`${event.message} (${event.filename || "page"})`);
});
window.addEventListener("unhandledrejection", (event) => {
  let reason = event.reason;
  try {
    reason = JSON.stringify(reason, Object.getOwnPropertyNames(reason ?? {}));
  } catch (error) {
    reason = String(reason);
  }
  window.__pageErrors.push(`unhandled rejection: ${reason}`);
});
"""
# A browser notice, not an error: the sections view re-measures itself after the
# card's text wraps differently at the final column width (a few pixels).
BENIGN = ("ResizeObserver loop completed with undelivered notifications",)


class BrowserFailure(AssertionError):
    pass


def check(condition: bool, message: str) -> None:
    if not condition:
        raise BrowserFailure(message)


def board_requests() -> dict:
    with urllib.request.urlopen(f"{BOARD}/control/requests", timeout=10) as response:
        return json.load(response)


def open_view(
    browser: Browser, view: str, cards: str, ready: str, scheme: str = "dark"
) -> tuple[Page, list[str]]:
    page = browser.new_page(
        locale="en-US", viewport={"width": 1280, "height": 820}, color_scheme=scheme
    )
    problems: list[str] = []
    page.add_init_script(CAPTURE_ERRORS)
    page.on(
        "console",
        lambda message: (
            message.type == "error"
            and "autodarts" in message.text.lower()
            and problems.append(f"console: {message.text}")
        ),
    )
    page.goto(f"{HA}/autodarts-demo/{view}")
    page.wait_for_function(
        f"() => ({cards})().some((card) => card.shadowRoot?.querySelector('{ready}'))",
        timeout=30000,
    )
    return page, problems


def open_board(browser: Browser, scheme: str = "dark") -> tuple[Page, list[str]]:
    return open_view(browser, "board", CARDS, ".board svg", scheme)


def page_errors(page: Page, problems: list[str]) -> list[str]:
    """Console errors from the card plus every page error except known notices."""
    recorded = page.evaluate("window.__pageErrors || []")
    return problems + [
        error for error in recorded if not any(text in error for text in BENIGN)
    ]


def fresh_loads(browser: Browser) -> None:
    # Home Assistant boots in parallel with the card module; every load must register it.
    for attempt in range(LOADS):
        page, problems = open_board(browser)
        check(page.evaluate(RENDERED) == 1, f"Load {attempt + 1}: card not rendered")
        errors = page_errors(page, problems)
        check(not errors, f"Load {attempt + 1}: {errors}")
        page.close()


def visit(browser: Browser) -> None:
    page, problems = open_board(browser)
    state = page.evaluate(CARD_STATE)
    expected = {
        "score": "115",
        "slots": ["T20", "S5", "Bull"],
        "latest": 2,
        "hits": 3,
        "darts": 3,
        "blinking": True,
        "status": "Remove your darts",
        "toggle": "Stop detection",
        "numbers": 20,
        "beds": 80,
        # The last completed visits, newest first.
        "recent": ["90", "112", "102", "125", "81"],
    }
    check(state == expected, f"Card state {state} != {expected}")

    commands = len(board_requests()["commands"])
    page.locator("autodarts-card button[data-action='toggle']").click()
    page.wait_for_function(
        f"() => ({CARD_STATE})().toggle === 'Start detection'", timeout=15000
    )
    new = board_requests()["commands"][commands:]
    check(
        [(c["method"], c["path"]) for c in new] == [("PUT", "/api/stop")],
        f"Stop sent {new}",
    )
    page.locator("autodarts-card button[data-action='toggle']").click()
    page.wait_for_function(
        f"() => ({CARD_STATE})().toggle === 'Stop detection'", timeout=15000
    )

    # Discarding detected darts needs a second tap within a few seconds.
    commands = len(board_requests()["commands"])
    reset = page.locator("autodarts-card button[data-action='reset']")
    reset.click()
    check(reset.text_content() == "Confirm?", "Reset did not ask for confirmation")
    check(
        len(board_requests()["commands"]) == commands, "Reset ran without confirmation"
    )
    reset.click()
    page.wait_for_function(f"() => ({CARD_STATE})().score === '0'", timeout=15000)
    new = board_requests()["commands"][commands:]
    check(
        [(c["method"], c["path"]) for c in new] == [("POST", "/api/reset")],
        f"Reset sent {new}",
    )
    errors = page_errors(page, problems)
    check(not errors, f"Console problems: {errors}")
    page.close()


def training(browser: Browser) -> None:
    page, problems = open_view(browser, "training", TRAINING_CARDS, ".heat-layer path")
    # The history of completed visits is loaded from the recorder.
    try:
        page.wait_for_function(
            f"() => ({TRAINING_STATE})().history === 5", timeout=15000
        )
    except PlaywrightTimeout:
        pass  # The comparison below reports what the card shows instead.
    state = page.evaluate(TRAINING_STATE)
    # Demo visits: 81, 125, 102, 112 and 90 points, plus 115 in progress.
    expected = {
        "average": "104.2",
        "darts": "18",
        "visits": "6",
        "heat": 11,
        "top": ["S20", "T20", "Bull", "S5", "25"],
        "history": 5,
        "highest": "125",
        # Darts, average and best visit of the two earlier sessions, newest first.
        "sessions": [["9", "86.0", "97"], ["6", "83.0", "140"]],
        "session": "End session",
        "state": "Session running",
    }
    check(state == expected, f"Training card state {state} != {expected}")

    # Ending a session needs a second tap; starting one does not.
    toggle = page.locator("autodarts-training-card button[data-action='session']")
    toggle.click()
    check(toggle.text_content() == "Confirm?", "Ending did not ask for confirmation")
    toggle.click()
    page.wait_for_function(
        f"() => ({TRAINING_STATE})().session === 'Start session'", timeout=30000
    )
    ended = page.evaluate(TRAINING_STATE)
    check(ended["state"].startswith("Session ended"), f"Session state {ended}")
    check(len(ended["sessions"]) == 3, f"Ended session missing: {ended['sessions']}")
    toggle.click()
    page.wait_for_function(f"() => ({TRAINING_STATE})().darts === '0'", timeout=30000)
    errors = page_errors(page, problems)
    check(not errors, f"Console problems: {errors}")
    page.close()


def status(browser: Browser) -> None:
    page, problems = open_view(browser, "status", STATUS_CARDS, ".camera")
    state = page.evaluate(STATUS_STATE)
    check(state["cameras"] == 3, f"Status card cameras: {state}")
    check(state["version"].startswith("Version "), f"Status card version: {state}")
    check(state["detection"] == "true", f"Status card detection: {state}")
    check(state["chips"] == 3, f"Status card connections: {state}")
    # Board Manager 2 describes its PC; the classic Board Manager does not.
    expected_info = (
        "Debian 13 · Intel Core i3-9100T · Detection 2.0.0" if GENERATION >= 2 else ""
    )
    check(state["info"] == expected_info, f"Status card board PC: {state}")

    commands = len(board_requests()["commands"])
    toggle = page.locator("autodarts-status-card .toggle")
    toggle.click()
    page.wait_for_function(
        f"() => ({STATUS_STATE})().detection === 'false'", timeout=15000
    )
    new = board_requests()["commands"][commands:]
    check(
        [(c["method"], c["path"]) for c in new] == [("PUT", "/api/stop")],
        f"Stop sent {new}",
    )
    toggle.click()
    page.wait_for_function(
        f"() => ({STATUS_STATE})().detection === 'true'", timeout=15000
    )

    # Restarting the Board Manager needs a second tap.
    restart = page.locator("autodarts-status-card button[data-action='restart']")
    commands = len(board_requests()["commands"])
    restart.click()
    check(restart.text_content() == "Confirm?", "Restart did not ask for confirmation")
    check(
        len(board_requests()["commands"]) == commands,
        "Restart ran without confirmation",
    )
    errors = page_errors(page, problems)
    check(not errors, f"Console problems: {errors}")
    page.close()


def strategy(browser: Browser) -> None:
    """The generated dashboard shows each card in its view."""
    page = browser.new_page(locale="en-US", viewport={"width": 1280, "height": 900})
    page.add_init_script(CAPTURE_ERRORS)
    for view, cards, ready in (
        ("live", CARDS, ".board svg"),
        ("training", TRAINING_CARDS, ".heat-layer"),
        ("board", STATUS_CARDS, ".camera"),
    ):
        page.goto(f"{HA}/autodarts-auto/{view}")
        page.wait_for_function(
            f"() => ({cards})().some((card) => card.shadowRoot?.querySelector('{ready}'))",
            timeout=30000,
        )
    errors = page_errors(page, [])
    check(not errors, f"Console problems: {errors}")
    page.close()


def editor(
    browser: Browser,
    view: str = "board",
    cards: str = CARDS,
    ready: str = ".board svg",
    tag: str = "autodarts-card-editor",
    rows: int = 5,
) -> None:
    page, problems = open_view(browser, view, cards, ready)
    page.goto(f"{HA}/autodarts-demo/{view}?edit=1")
    page.wait_for_function(
        f"() => ({cards})().some((card) => card.shadowRoot?.querySelector('{ready}'))",
        timeout=30000,
    )
    page.evaluate(
        f"() => ({cards})()[0].dispatchEvent(new CustomEvent('ll-edit-card',"
        " {bubbles: true, composed: true, detail: {path: [0, 0, 0]}}))"
    )
    form = page.locator(f"{tag} > ha-form")
    form.wait_for(timeout=15000)
    fields = form.evaluate("(element) => element.schema.length")
    check(fields == rows, f"{tag} schema has {fields} rows")
    page.keyboard.press("Escape")
    errors = page_errors(page, problems)
    check(not errors, f"Console problems: {errors}")
    page.close()


def light_theme(browser: Browser) -> None:
    page, problems = open_board(browser, "light")
    check(page.evaluate(RENDERED) == 1, "Card not rendered in the light theme")
    errors = page_errors(page, problems)
    check(not errors, f"Console problems: {errors}")
    page.close()


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        steps = [
            ("fresh loads", lambda: fresh_loads(browser)),
            # The training card reads the demo session before any control changes it.
            ("training card", lambda: training(browser)),
            ("live card", lambda: visit(browser)),
            ("status card", lambda: status(browser)),
            ("automatic dashboard", lambda: strategy(browser)),
            ("live card editor", lambda: editor(browser)),
            (
                "training card editor",
                lambda: editor(
                    browser,
                    "training",
                    TRAINING_CARDS,
                    ".heat-layer",
                    "autodarts-training-card-editor",
                    5,
                ),
            ),
            (
                "status card editor",
                lambda: editor(
                    browser,
                    "status",
                    STATUS_CARDS,
                    ".toggle",
                    "autodarts-status-card-editor",
                    3,
                ),
            ),
            ("light theme", lambda: light_theme(browser)),
        ]
        for name, step in steps:
            # A failure then names the step, not only a timeout deep in Playwright.
            print(f"Browser step: {name}", flush=True)
            step()
        browser.close()
    print(
        "Browser check passed: card registration on every load, visit, highlights, "
        "controls with confirmation, last visits, training heatmap, history and "
        "sessions, board status, "
        "the generated dashboard, all three editors and light theme."
    )


if __name__ == "__main__":
    main()
