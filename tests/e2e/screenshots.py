"""Capture documentation screenshots and the visit animation from the demo instance.

Runs in the Playwright container on the demo's Compose network (see screenshots.sh).
Every image shows the synthetic demo board, so no personal data can appear.
"""

from __future__ import annotations

import io
import json
import os
import sys
import urllib.request
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright

HA = "http://homeassistant:8123"
BOARD = "http://board-mock:3180"
LANGUAGE = os.environ.get("DEMO_LANGUAGE", "en")
OUTPUT = Path(os.environ.get("OUTPUT", "/repo/docs/images")) / LANGUAGE
LOCALE = {"en": "en-US", "de": "de-DE"}[LANGUAGE]

# Demo darts as the Board Manager reports them (see demo.py).
T20 = {
    "segment": {"name": "T20", "number": 20, "multiplier": 3, "bed": "Triple"},
    "coords": {"x": 0.035, "y": 0.608},
}
S5 = {
    "segment": {"name": "S5", "number": 5, "multiplier": 1, "bed": "SingleOuter"},
    "coords": {"x": -0.24, "y": 0.76},
}
BULL = {
    "segment": {"name": "Bull", "number": 25, "multiplier": 2, "bed": "Double"},
    "coords": {"x": 0.012, "y": -0.02},
}

FIND_CARDS = """
() => {
  const cards = [];
  (function collect(root) {
    root.querySelectorAll('autodarts-card').forEach((card) => cards.push(card));
    root.querySelectorAll('*').forEach((el) => el.shadowRoot && collect(el.shadowRoot));
  })(document);
  return cards;
}
"""

# Pauses the card animations at a given time, so blinking beds render deterministically.
SEEK = (
    "(time) => { for (const card of ("
    + FIND_CARDS
    + ")()) { for (const animation of card.shadowRoot.getAnimations()) {"
    " animation.pause(); animation.currentTime = time; } } }"
)
EDIT_CARD = (
    "() => { const [card] = ("
    + FIND_CARDS
    + ")(); card.dispatchEvent(new CustomEvent('ll-edit-card', {bubbles: true,"
    " composed: true, detail: {path: [0, 0, 0]}})); }"
)


def control(changes: dict) -> None:
    request = urllib.request.Request(
        f"{BOARD}/control/state",
        data=json.dumps(changes).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(request, timeout=10).read()


def wait_for_score(page: Page, score: str) -> None:
    page.wait_for_function(
        f"() => ({FIND_CARDS})().some((c) => c.shadowRoot.querySelector('.score')?.textContent === '{score}')",
        timeout=15000,
    )


def open_dashboard(page: Page, view: str) -> None:
    page.goto(f"{HA}/autodarts-demo/{view}")
    page.wait_for_function(
        f"() => ({FIND_CARDS})().some((c) => c.shadowRoot.querySelector('.board svg'))",
        timeout=60000,
    )
    page.wait_for_timeout(1200)


def peak(page: Page) -> None:
    # The end of a blink cycle shows the highlight at full strength.
    page.evaluate(SEEK, 800)


def card_shot(page: Page, name: str, index: int = 0) -> None:
    card = page.locator("autodarts-card").nth(index)
    card.screenshot(path=str(OUTPUT / f"{name}.png"), animations="allow")
    print(f"saved {OUTPUT / name}.png")


def page_shot(page: Page, name: str) -> None:
    page.screenshot(path=str(OUTPUT / f"{name}.png"))
    print(f"saved {OUTPUT / name}.png")


def visit_animation(page: Page) -> None:
    """Darts landing one by one, then the takeout, as an animated GIF."""
    frames: list[Image.Image] = []
    durations: list[int] = []
    card = page.locator("autodarts-card").first

    def capture(count: int, step: int = 100, hold: int | None = None) -> None:
        for index in range(count):
            page.evaluate(SEEK, index * step)
            frames.append(Image.open(io.BytesIO(card.screenshot(animations="allow"))))
            durations.append(hold if hold and index == count - 1 else step)

    control({"status": "Throw", "event": "Takeout finished", "throws": []})
    wait_for_score(page, "0")
    capture(1, hold=900)
    for darts, score in (([T20], "60"), ([T20, S5], "65"), ([T20, S5, BULL], "115")):
        control({"event": "Throw detected", "throws": darts})
        wait_for_score(page, score)
        capture(16)
    capture(1, hold=900)
    control({"status": "Takeout in progress", "event": "Takeout started"})
    page.wait_for_timeout(700)
    capture(8)
    control({"status": "Throw", "event": "Takeout finished", "throws": []})
    wait_for_score(page, "0")
    capture(1, hold=1200)

    palette = [
        frame.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        for frame in frames
    ]
    target = OUTPUT / "card-visit.gif"
    palette[0].save(
        target,
        save_all=True,
        append_images=palette[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"saved {target} ({target.stat().st_size // 1024} KiB, {len(frames)} frames)")
    # Restore the demo visit for the remaining screenshots.
    for darts in ([T20], [T20, S5], [T20, S5, BULL]):
        control({"event": "Throw detected", "throws": darts})
    wait_for_score(page, "115")


def config_flow(page: Page) -> None:
    page.goto(f"{HA}/config/integrations/dashboard/add?domain=autodarts")
    dialog = page.locator("dialog-data-entry-flow")
    menu = page.get_by_text(
        "Local board" if LANGUAGE == "en" else "Lokales Board", exact=True
    )
    menu.wait_for(timeout=30000)
    page.wait_for_timeout(800)
    page_shot(page, "setup-menu")
    menu.click()
    title = "Connect local board" if LANGUAGE == "en" else "Lokales Board verbinden"
    page.get_by_text(title, exact=True).wait_for(timeout=15000)
    page.wait_for_timeout(800)
    page_shot(page, "setup-local")
    page.keyboard.press("Escape")
    dialog.wait_for(state="detached", timeout=15000)


def device_page(page: Page) -> None:
    open_dashboard(page, "board")
    device_id = page.evaluate(
        "() => Object.values(document.querySelector('home-assistant').hass.devices)"
        ".find((d) => d.identifiers.some((i) => i[0] === 'autodarts')).id"
    )
    page.goto(f"{HA}/config/devices/device/{device_id}")
    page.get_by_text("Autodarts Board").first.wait_for(timeout=30000)
    page.wait_for_timeout(2500)
    page_shot(page, "device")


def editor(page: Page) -> None:
    page.goto(f"{HA}/autodarts-demo/board?edit=1")
    page.wait_for_timeout(2500)
    page.evaluate(EDIT_CARD)
    page.locator("autodarts-card-editor").wait_for(timeout=15000)
    page.wait_for_timeout(2000)
    peak(page)
    page_shot(page, "card-editor")
    page.keyboard.press("Escape")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for scheme, suffix in (("dark", ""), ("light", "-light")):
            context = browser.new_context(
                viewport={"width": 1280, "height": 820},
                device_scale_factor=2,
                locale=LOCALE,
                color_scheme=scheme,
            )
            page = context.new_page()
            open_dashboard(page, "board")
            wait_for_score(page, "115")
            peak(page)
            card_shot(page, f"card{suffix}")
            if scheme == "dark":
                open_dashboard(page, "styles")
                peak(page)
                card_shot(page, "card-autodarts-style", 0)
                card_shot(page, "card-board-only", 1)
                editor(page)
                config_flow(page)
                device_page(page)
            context.close()

        mobile = browser.new_context(
            viewport={"width": 412, "height": 915},
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True,
            locale=LOCALE,
            color_scheme="dark",
        )
        page = mobile.new_page()
        open_dashboard(page, "board")
        peak(page)
        card_shot(page, "card-mobile")
        mobile.close()

        animation = browser.new_context(
            viewport={"width": 1100, "height": 700},
            device_scale_factor=1,
            locale=LOCALE,
            color_scheme="dark",
        )
        page = animation.new_page()
        open_dashboard(page, "board")
        visit_animation(page)
        animation.close()
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
