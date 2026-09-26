"""Live camera streams: relayed from Board Manager 2, snapshots everywhere else."""

from unittest.mock import patch

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.autodarts.camera import AutodartsCamera
from custom_components.autodarts.errors import AutodartsConnectionError

from .local_helpers import BASE
from .test_board_manager_2 import setup_v2
from .test_local_setup import entity_id, setup_local

MJPEG = "multipart/x-mixed-replace; boundary=frame"
FRAME = b"--frame\r\nContent-Type: image/jpeg\r\n\r\njpeg\r\n"
SNAPSHOTS = "homeassistant.components.camera.Camera.handle_async_mjpeg_stream"


async def test_board_manager_2_relays_the_live_stream(
    hass, aioclient_mock, hass_client
):
    entry = await setup_v2(hass, aioclient_mock)
    camera = entity_id(hass, "camera", "camera_0")
    er.async_get(hass).async_update_entity(camera, disabled_by=None)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    aioclient_mock.get(
        f"{BASE}/api/streams/cams/0", content=FRAME, headers={"Content-Type": MJPEG}
    )
    client = await hass_client()
    response = await client.get(f"/api/camera_proxy_stream/{camera}")
    assert response.status == 200
    assert response.headers["Content-Type"] == MJPEG
    assert await response.read() == FRAME
    streams = [call for call in aioclient_mock.mock_calls if "streams" in str(call[1])]
    assert [(call[0], call[1].path) for call in streams] == [
        ("GET", "/api/streams/cams/0")
    ]


@pytest.mark.parametrize(
    ("status", "headers"),
    [(404, {}), (200, {"Content-Type": "text/html"})],
)
async def test_a_missing_stream_falls_back_to_snapshots(
    hass, aioclient_mock, status, headers
):
    entry = await setup_v2(hass, aioclient_mock)
    aioclient_mock.get(
        f"{BASE}/api/streams/cams/1", status=status, text="none", headers=headers
    )
    client = entry.runtime_data.local.client
    with pytest.raises(AutodartsConnectionError, match="No camera stream"):
        await client.open_camera_stream(1)
    camera = AutodartsCamera(entry.runtime_data.local, 1)
    with patch(SNAPSHOTS, return_value=None) as snapshots:
        assert await camera.handle_async_mjpeg_stream(object()) is None
    snapshots.assert_called_once()


async def test_board_manager_1_sends_snapshots_without_asking(hass, aioclient_mock):
    entry = await setup_local(hass, aioclient_mock)
    camera = AutodartsCamera(entry.runtime_data.local, 0)
    aioclient_mock.clear_requests()
    with patch(SNAPSHOTS, return_value=None) as snapshots:
        await camera.handle_async_mjpeg_stream(object())
    snapshots.assert_called_once()
    assert not aioclient_mock.mock_calls
