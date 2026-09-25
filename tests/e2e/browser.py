"""Verify the dashboard card in a real browser against the demo instance.

Runs in the Playwright container on the demo's Compose network (see browser.sh).
"""

from __future__ import annotations

import json
import urllib.request

from playwright.sync_api import Browser, Page, sync_playwright

HA = "http://homeassistant:8123"
BOARD = "http://board-mock:3180"
LOADS = 5

CARDS = """
() => {
  const cards = [];
  (function collect(root) {
    root.querySelectorAll('autodarts-card').forEach((card) => cards.push(card));
    root.querySelectorAll('*').forEach((el) => el.shadowRoot && collect(el.shadowRoot));
  })(document);
  return cards;
}
"""
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


def open_board(browser: Browser, scheme: str = "dark") -> tuple[Page, list[str]]:
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
    page.goto(f"{HA}/autodarts-demo/board")
    page.wait_for_function(RENDERED, timeout=30000)
    return page, problems


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


def editor(browser: Browser) -> None:
    page, problems = open_board(browser)
    page.goto(f"{HA}/autodarts-demo/board?edit=1")
    page.wait_for_function(RENDERED, timeout=30000)
    page.evaluate(
        f"() => ({CARDS})()[0].dispatchEvent(new CustomEvent('ll-edit-card',"
        " {bubbles: true, composed: true, detail: {path: [0, 0, 0]}}))"
    )
    form = page.locator("autodarts-card-editor > ha-form")
    form.wait_for(timeout=15000)
    fields = form.evaluate("(element) => element.schema.length")
    check(fields == 5, f"Editor schema has {fields} rows")
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
        fresh_loads(browser)
        visit(browser)
        editor(browser)
        light_theme(browser)
        browser.close()
    print(
        "Browser check passed: card registration on every load, visit, highlights, "
        "controls with confirmation, editor and light theme."
    )


if __name__ == "__main__":
    main()
