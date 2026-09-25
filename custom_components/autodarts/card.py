"""Serve the bundled Lovelace card and load it on every dashboard."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

CARD_URL = f"/{DOMAIN}/autodarts-card.js"
CARD_PATH = Path(__file__).parent / "frontend" / "autodarts-card.js"


async def async_register_card(hass: HomeAssistant) -> None:
    """Make custom:autodarts-card available without a manual dashboard resource."""
    if hass.http is None or "frontend" not in hass.config.components:
        return
    version = (await async_get_integration(hass, DOMAIN)).version
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=True)]
    )
    # The version changes the URL on updates, so cached cards are never stale.
    add_extra_js_url(hass, f"{CARD_URL}?v={version}")
