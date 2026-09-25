"""The Autodarts integration, with independent local and cloud connections."""

from __future__ import annotations

from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .api import AutodartsCloudClient
from .card import async_register_card
from .const import (
    CONF_BOARD_ID,
    CONF_CLIENT_ID,
    CONF_HOST,
    CONF_LOCAL_ONLY,
    CONF_PORT,
    CONF_TOKEN,
    DEFAULT_PORT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import AutodartsDataUpdateCoordinator
from .local_api import AutodartsLocalClient
from .local_coordinator import AutodartsLocalCoordinator
from .runtime import AutodartsRuntimeData

type AutodartsConfigEntry = ConfigEntry[AutodartsRuntimeData]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Provide the dashboard card once, independent of config entries."""
    await async_register_card(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AutodartsConfigEntry) -> bool:
    """Local controls remain usable even if cloud authentication fails."""
    session = async_get_clientsession(hass)
    runtime = AutodartsRuntimeData()
    local_error: Exception | None = None

    async def setup_local(host: str, port: int) -> None:
        nonlocal local_error
        local_error = None
        runtime.local = AutodartsLocalCoordinator(
            hass,
            AutodartsLocalClient(host, port, session),
            entry.data[CONF_BOARD_ID],
            entry,
        )
        try:
            await runtime.local.async_config_entry_first_refresh()
        except ConfigEntryNotReady as err:
            local_error = err

    if host := entry.data.get(CONF_HOST):
        await setup_local(host, entry.data.get(CONF_PORT, DEFAULT_PORT))

    if not entry.data.get(CONF_LOCAL_ONLY, False):

        def persist_token(token: dict) -> None:
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_TOKEN: token}
            )

        try:
            if not entry.data.get(CONF_CLIENT_ID):
                raise ConfigEntryAuthFailed(
                    "Relink Autodarts using a registered device-flow client ID"
                )
            runtime.cloud = AutodartsDataUpdateCoordinator(
                hass,
                cloud=AutodartsCloudClient(
                    session,
                    entry.data[CONF_TOKEN],
                    entry.data[CONF_CLIENT_ID],
                    persist_token,
                ),
                board_id=entry.data[CONF_BOARD_ID],
                entry=entry,
            )
            await runtime.cloud.async_config_entry_first_refresh()
        except ConfigEntryAuthFailed:
            if runtime.local is None or local_error is not None:
                raise
            entry.async_start_reauth(hass)
        except ConfigEntryNotReady:
            if runtime.local is None or local_error is not None:
                raise

        # Discover once during setup so local entities can be created immediately.
        if runtime.local is None and runtime.cloud and runtime.cloud.data:
            board_url = runtime.cloud.data.get("board", {}).get("ip") or ""
            for address in board_url.split(",") if isinstance(board_url, str) else []:
                try:
                    parsed = urlparse(address.strip())
                    if parsed.scheme == "http" and parsed.hostname:
                        await setup_local(parsed.hostname, parsed.port or DEFAULT_PORT)
                        if local_error is None:
                            hass.config_entries.async_update_entry(
                                entry,
                                data={
                                    **entry.data,
                                    CONF_HOST: parsed.hostname,
                                    CONF_PORT: parsed.port or DEFAULT_PORT,
                                },
                            )
                            break
                except ValueError:
                    continue
    elif runtime.local is None:
        raise ConfigEntryNotReady("Configure a local Board Manager address")
    elif local_error is not None:
        raise local_error

    entry.runtime_data = runtime
    if runtime.local:
        device = next(
            (
                device
                for device in dr.async_entries_for_config_entry(
                    dr.async_get(hass), entry.entry_id
                )
                if (DOMAIN, entry.data[CONF_BOARD_ID]) in device.identifiers
            ),
            None,
        )
        board = (runtime.cloud.data or {}).get("board", {}) if runtime.cloud else {}
        runtime.local.device_name = board.get("name") or (
            device.name if device and device.name else "Autodarts Board"
        )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if runtime.local:
        runtime.local.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AutodartsConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: AutodartsConfigEntry) -> None:
    """Deleting the integration also deletes its local training session."""
    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.training").async_remove()
