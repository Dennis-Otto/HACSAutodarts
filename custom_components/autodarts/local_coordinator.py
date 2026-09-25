"""Combine local push notifications, HTTP recovery and persistent training counts."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Coroutine
from contextlib import suppress
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .camera_health import CameraHealth
from .const import DOMAIN
from .errors import AutodartsApiError
from .local_api import AutodartsEndpointMissing, AutodartsLocalClient
from .training import TrainingSession

_LOGGER = logging.getLogger(__name__)
# Poll quickly without realtime events; with them, polling only reconciles.
POLL_INTERVAL = timedelta(seconds=2)
STREAM_POLL_INTERVAL = timedelta(seconds=30)
MOTION_FLAGS = (
    "isWaiting",
    "isStable",
    "isDart",
    "isHand",
    "isTakeoutPartial",
    "isTakeoutFull",
)
EVENT_TYPES = [
    "dart_detected",
    "dart_corrected",
    "takeout_started",
    "takeout_finished",
    "status_changed",
]


class AutodartsLocalCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Keep controls local and reconcile push notifications with periodic reads."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AutodartsLocalClient,
        board_id: str,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_local",
            config_entry=entry,
            update_interval=POLL_INTERVAL,
            # Show the result of consecutive user actions without a long cooldown.
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=1, immediate=True
            ),
        )
        self.client = client
        self.board_id = board_id
        self.device_name = "Autodarts Board"
        self.event_signal = f"{DOMAIN}_{entry.entry_id}_event"
        self.training = TrainingSession()
        self._store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.training")
        self._training_dirty = False
        self._health = CameraHealth()
        self._settings: dict[str, Any] = {}
        self._version: str | None = None
        self._metadata_updated = 0.0
        self._identity_valid = True
        self._action_lock = asyncio.Lock()
        self._stream_task: asyncio.Task | None = None
        self.stream_connected = False
        self._revisions: dict[str, int] = {}
        self._observed_state: dict | None = None
        self._observed_motion: dict | None = None
        self._taking_out = False

    async def _async_setup(self) -> None:
        saved = await self._store.async_load()
        self.training.restore(saved)
        if saved is None:
            self._save_training()

    def _save_training(self) -> None:
        self._training_dirty = True
        self._store.async_delay_save(self.training.snapshot, 5)

    @callback
    def async_start(self) -> None:
        if self._stream_task is None:
            self._stream_task = self.config_entry.async_create_background_task(
                self.hass, self._listen(), f"{DOMAIN} local events"
            )

    async def async_shutdown(self) -> None:
        await super().async_shutdown()
        if self._stream_task:
            self._stream_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._stream_task
            self._stream_task = None
        if self._training_dirty:
            await self._store.async_save(self.training.snapshot())
            self._training_dirty = False

    async def _listen(self) -> None:
        delay = 1
        while not self._shutdown_requested:
            connected_at = None
            try:
                async for kind, payload in self.client.events():
                    if self._shutdown_requested:
                        return
                    if kind == "connected":
                        self.stream_connected = True
                        self.update_interval = STREAM_POLL_INTERVAL
                        connected_at = time.monotonic()
                        self.async_update_listeners()
                        continue
                    self.async_receive(kind, payload)
            except AutodartsApiError:
                _LOGGER.debug(
                    "Local event stream unavailable; HTTP polling remains active"
                )
            except Exception:
                # Never let one bad message end realtime updates until a reload.
                _LOGGER.exception("Unexpected error in the local event stream")
            finally:
                self.stream_connected = False
                self.update_interval = POLL_INTERVAL
                if connected_at is not None:
                    self._baseline_after_gap()
                if not self._shutdown_requested:
                    self.async_update_listeners()
            if connected_at is not None and not self._shutdown_requested:
                # Resume fast polling right away instead of after the long interval.
                await self.async_request_refresh()
            if connected_at is not None and time.monotonic() - connected_at >= 30:
                delay = 1
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)

    async def _optional(self, operation: Coroutine) -> Any:
        """Unsupported endpoints read as empty; a failed read returns None."""
        try:
            return await operation
        except AutodartsEndpointMissing:
            return {}
        except AutodartsApiError:
            return None

    def _baseline_after_gap(self) -> None:
        """A disconnected visit cannot reliably be distinguished from a new one."""
        self.training.baseline({})
        self._observed_state = None
        self._observed_motion = None
        self._taking_out = False

    @staticmethod
    def _motion(payload: dict) -> dict:
        return {
            key: payload[key]
            for key in MOTION_FLAGS
            if isinstance(payload.get(key), bool)
        }

    def _emit(self, kind: str, attributes: dict, source: str) -> None:
        # Publish the corresponding sensor states before event consumers run.
        self.hass.loop.call_soon(
            async_dispatcher_send,
            self.hass,
            self.event_signal,
            kind,
            {**attributes, "source": source},
        )

    def _start_takeout(self, source: str) -> None:
        if not self._taking_out:
            self._taking_out = True
            self._emit("takeout_started", {}, source)

    def _finish_takeout(self, source: str) -> None:
        if self._taking_out:
            self._taking_out = False
            self._emit("takeout_finished", {}, source)

    def _process(self, data: dict, fields: set[str], source: str) -> None:
        previous_training = self.training.snapshot()
        state = data.get("local", {})
        if "local" in fields:
            previous = self._observed_state
            for kind, attributes in self.training.observe(state):
                self._emit(kind, attributes, source)
            if previous is not None:
                status = state.get("status")
                if isinstance(status, str) and status != previous.get("status"):
                    self._emit("status_changed", {"status": status}, source)
                marker = str(state.get("event") or status or "").lower()
                if state.get("running") is not True or str(status).lower() in (
                    "calibrating",
                    "starting",
                    "stopping",
                    "stopped",
                    "error",
                ):
                    self._taking_out = False
                elif marker in ("takeout started", "takeout in progress"):
                    self._start_takeout(source)
                elif marker == "takeout finished" or state.get("numThrows") == 0:
                    self._finish_takeout(source)
            self._observed_state = state
        if "motion" in fields:
            motion = data.get("motion", {})
            previous = self._observed_motion
            if (
                previous is not None
                and state.get("running") is True
                and str(state.get("status", "")).lower()
                not in ("calibrating", "starting", "stopping", "stopped", "error")
            ):
                started = any(
                    motion.get(key) is True and previous.get(key) is not True
                    for key in ("isHand", "isTakeoutPartial")
                )
                count = state.get("numThrows")
                if started and type(count) is int and count > 0:
                    self._start_takeout(source)
                if (
                    motion.get("isTakeoutFull") is True
                    and previous.get("isTakeoutFull") is not True
                ):
                    self._finish_takeout(source)
            self._observed_motion = motion
        data["training"] = self.training.snapshot()
        if data["training"] != previous_training:
            self._save_training()
        data["camera_problems"] = self._health.update(data, time.monotonic())

    @callback
    def async_receive(self, kind: str, payload: dict) -> None:
        """Merge a push message; high-rate FPS telemetry is published by the poll."""
        if (
            not isinstance(payload, dict)
            or not self._identity_valid
            or self._shutdown_requested
        ):
            return
        data = dict(self.data or {})
        if kind == "state":
            if not isinstance(payload.get("running"), bool):
                return
            field, value = "local", payload
        elif kind == "motion_state":
            field, value = "motion", self._motion(payload)
        elif kind == "cam_state":
            field, value = (
                "camera_state",
                {
                    key: payload[key]
                    for key in ("isOpened", "isRunning")
                    if isinstance(payload.get(key), bool)
                },
            )
        elif kind == "stats":
            field, value = "stats", payload
        elif kind == "cam_stats":
            index, fps = payload.get("id"), payload.get("fps")
            count = self._settings.get("camera_count", 0)
            if (
                type(index) is not int
                or not 0 <= index < count
                or type(fps) not in (int, float)
            ):
                return
            current_frames = data.get("camera_stats", {}).get("fps")
            frames = list(current_frames) if isinstance(current_frames, list) else []
            frames.extend([None] * max(0, count - len(frames)))
            frames[index] = fps
            field, value = "camera_stats", {"fps": frames}
        else:
            return
        self._revisions[field] = self._revisions.get(field, 0) + 1
        changed = data.get(field) != value
        data[field] = value
        self._process(data, {field}, "websocket")
        self.data = data
        recovered = field == "local" and not self.last_update_success
        if recovered:
            _LOGGER.info("Local Board Manager is available again")
        if field == "local":
            self.last_update_success = True
        if (changed or recovered) and field not in ("stats", "camera_stats"):
            self.async_update_listeners()

    async def _async_update_data(self) -> dict[str, Any]:
        revisions = dict(self._revisions)
        try:
            state = await self.client.get_state()
        except AutodartsApiError as err:
            if self.stream_connected and self.data:
                # Realtime events still arrive, so a missed poll is no outage.
                _LOGGER.debug("Board Manager missed a poll; realtime events continue")
                return dict(self.data)
            self._health = CameraHealth()
            if not self.stream_connected:
                self._baseline_after_gap()
            raise UpdateFailed("Local Board Manager unavailable") from err
        stats, camera_stats, motion, camera_state = await asyncio.gather(
            self._optional(self.client.get_stats()),
            self._optional(self.client.get_camera_stats()),
            self._optional(self.client.get_motion_state()),
            self._optional(self.client.get_camera_state()),
        )
        if (
            not self._metadata_updated
            or time.monotonic() - self._metadata_updated >= 30
        ):
            config, version = await asyncio.gather(
                self._optional(self.client.get_config()),
                self._optional(self.client.get_version()),
            )
            if config:
                self._identity_valid = (
                    config.get("board_id", self.board_id) == self.board_id
                )
            if not self._identity_valid:
                raise UpdateFailed("Local address belongs to a different board")
            if config is not None:
                # A failed read keeps the last settings instead of hiding controls.
                self._settings = config
            previous_version = self._version
            self._version = version or self._version
            if previous_version and self._version != previous_version:
                self._update_device_version()
            self._metadata_updated = time.monotonic()
        data = dict(self.data or {})
        fields = set()
        for field, value in {
            "local": state,
            "stats": stats,
            "camera_stats": camera_stats,
            "motion": None if motion is None else self._motion(motion),
            "camera_state": camera_state,
        }.items():
            if value is None and field in data:
                continue  # A failed optional read keeps the last known value.
            # A completed HTTP read must not roll back a newer socket message.
            if self._revisions.get(field, 0) == revisions.get(field, 0):
                data[field] = value or {}
                fields.add(field)
        data.update(settings=self._settings, version=self._version)
        self._process(data, fields, "poll")
        return data

    @callback
    def _update_device_version(self) -> None:
        """Show a Board Manager update on the device page without a reload."""
        registry = dr.async_get(self.hass)
        device = registry.async_get_device_by_identifier(
            (DOMAIN, self.board_id), self.config_entry.entry_id
        )
        if device and device.sw_version != self._version:
            registry.async_update_device(device.id, sw_version=self._version)

    async def async_reset_training(self) -> None:
        self.training.reset((self.data or {}).get("local", {}))
        snapshot = self.training.snapshot()
        await self._store.async_save(snapshot)
        self._training_dirty = self.training.snapshot() != snapshot
        self.data = {**(self.data or {}), "training": self.training.snapshot()}
        self.async_update_listeners()

    async def async_action(
        self, action: Callable[[], Coroutine[Any, Any, None]]
    ) -> None:
        async with self._action_lock:
            try:
                await action()
            except AutodartsApiError as err:
                raise HomeAssistantError(
                    "Local board action failed. Check the board connection and Board Manager."
                ) from err
            self._metadata_updated = 0
            await self.async_request_refresh()
