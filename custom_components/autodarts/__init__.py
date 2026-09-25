"""The Autodarts integration, with independent local and cloud connections."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
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
from .errors import AutodartsApiError
from .local_api import AutodartsLocalClient
from .local_coordinator import AutodartsLocalCoordinator
from .runtime import AutodartsConfigEntry, AutodartsRuntimeData

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# Entities that only one Board Manager generation provides.
V1_ONLY = (("switch", "upstream"), ("button", "connect"), ("button", "disconnect"))
V2_ONLY = (
    ("binary_sensor", "cloud_link"),
    ("sensor", "cpu_usage"),
    ("sensor", "memory_usage"),
    ("update", "board_software"),
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Provide the dashboard card once, independent of config entries."""
    await async_register_card(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AutodartsConfigEntry) -> bool:
    """Local controls remain usable even if cloud authentication fails."""
    session = async_get_clientsession(hass)
    runtime = AutodartsRuntimeData()
    local_error: Exception | None = None

    def local_coordinator(host: str, port: int) -> AutodartsLocalCoordinator:
        return AutodartsLocalCoordinator(
            hass,
            AutodartsLocalClient(host, port, session),
            entry.data[CONF_BOARD_ID],
            entry,
        )

    async def discover_local(addresses: object) -> bool:
        """Adopt the first address reported by the cloud that answers as this board."""
        for address in addresses.split(",") if isinstance(addresses, str) else []:
            try:
                parsed = urlparse(address.strip())
                port = parsed.port or DEFAULT_PORT
            except ValueError:
                continue
            if parsed.scheme != "http" or not parsed.hostname:
                continue
            if (parsed.hostname, port) == (
                entry.data.get(CONF_HOST),
                entry.data.get(CONF_PORT, DEFAULT_PORT),
            ):
                continue
            candidate = local_coordinator(parsed.hostname, port)
            try:
                await candidate.async_config_entry_first_refresh()
            except ConfigEntryNotReady:
                # Discard failed candidates, including their timers and store.
                await candidate.async_shutdown()
                continue
            if runtime.local is not None:
                await runtime.local.async_shutdown()
            runtime.local = candidate
            hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, CONF_HOST: parsed.hostname, CONF_PORT: port},
            )
            return True
        return False

    if host := entry.data.get(CONF_HOST):
        runtime.local = local_coordinator(host, entry.data.get(CONF_PORT, DEFAULT_PORT))
        try:
            await runtime.local.async_config_entry_first_refresh()
        except ConfigEntryNotReady as err:
            # Entities stay and recover when the board answers again.
            local_error = err

    if not entry.data.get(CONF_LOCAL_ONLY, False):

        def persist_token(token: dict[str, Any]) -> None:
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_TOKEN: token}
            )

        try:
            if not entry.data.get(CONF_CLIENT_ID):
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN, translation_key="relink_required"
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
            if runtime.local is None:
                raise
            # A configured board keeps working locally while the login is renewed.
            entry.async_start_reauth(hass)
        except ConfigEntryNotReady:
            if runtime.local is None or local_error is not None:
                raise

        # The cloud knows the board's current address: use it when none is set or
        # the stored one no longer answers, e.g. after a DHCP change.
        if (runtime.local is None or local_error is not None) and (
            runtime.cloud and runtime.cloud.data
        ):
            if await discover_local(runtime.cloud.data.get("board", {}).get("ip")):
                local_error = None
    elif runtime.local is None:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="no_local_address"
        )
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
    if runtime.local:
        runtime.local.setup_generation = runtime.local.generation or 1
        _remove_other_generation(hass, entry, runtime.local.board_manager_2)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if runtime.local:
        runtime.local.async_start()
    return True


def _remove_other_generation(
    hass: HomeAssistant, entry: ConfigEntry, board_manager_2: bool
) -> None:
    """Remove entities of the other Board Manager generation after a change."""
    registry = er.async_get(hass)
    for platform, key in V1_ONLY if board_manager_2 else V2_ONLY:
        entity_id = registry.async_get_entity_id(
            platform, DOMAIN, f"{entry.data[CONF_BOARD_ID]}_{key}"
        )
        if entity_id:
            registry.async_remove(entity_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Upgrade version 1 entries, which stored a board address or a password."""
    if entry.version > 2:
        return False
    if entry.version == 2:
        return True
    data = dict(entry.data)
    board_id = data.get(CONF_BOARD_ID)
    host = data.get(CONF_HOST)
    port = data.get(CONF_PORT, DEFAULT_PORT)
    if not board_id and host:
        client = AutodartsLocalClient(host, port, async_get_clientsession(hass))
        try:
            board_id = (await client.get_config()).get(CONF_BOARD_ID)
        except AutodartsApiError:
            board_id = None
    if not board_id:
        # Retried at the next start, so a board that is switched off is no problem.
        _LOGGER.warning(
            "Cannot migrate the Autodarts entry %s yet: the board at %s does not answer",
            entry.title,
            host,
        )
        return False
    # Version 1 cloud entries stored the account password; never keep it.
    new = {CONF_BOARD_ID: board_id}
    if host:
        new |= {CONF_HOST: host, CONF_PORT: port, CONF_LOCAL_ONLY: True}
    hass.config_entries.async_update_entry(
        entry, data=new, unique_id=board_id, version=2
    )
    _LOGGER.info("Migrated the Autodarts entry %s to version 2", entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AutodartsConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: AutodartsConfigEntry) -> None:
    """Deleting the integration also deletes its local training session."""
    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.training").async_remove()
    for issue in ("wrong_board", "board_manager_1"):
        ir.async_delete_issue(hass, DOMAIN, f"{issue}_{entry.entry_id}")
