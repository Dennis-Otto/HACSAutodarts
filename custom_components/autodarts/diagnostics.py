"""Diagnostics contain local status only; never cloud tokens or board API keys."""

from homeassistant.components.diagnostics import async_redact_data

from .const import CONF_LOCAL_ONLY


async def async_get_config_entry_diagnostics(hass, entry):
    runtime = entry.runtime_data
    return {
        "local": async_redact_data(
            runtime.local.data if runtime.local else None, {"board_id"}
        ),
        "local_available": bool(runtime.local and runtime.local.last_update_success),
        "cloud_configured": not entry.data.get(CONF_LOCAL_ONLY, False),
        "cloud_available": bool(runtime.cloud and runtime.cloud.last_update_success),
        "realtime_connected": bool(runtime.local and runtime.local.stream_connected),
    }
