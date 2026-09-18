"""A camera alarm requires sustained zero FPS during active detection."""

import pytest

from custom_components.autodarts.camera_health import CameraHealth


def data(fps=None, running=True, status="Throw", cameras=True):
    return {
        "settings": {"camera_count": 3},
        "local": {"running": running, "status": status},
        "camera_state": {"isRunning": cameras},
        "camera_stats": {"fps": [30, 0, 30] if fps is None else fps},
    }


def test_sustained_failure_grace_period_and_recovery():
    health = CameraHealth()
    assert health.update(data(), 100) == [False, False, False]
    assert health.update(data(), 114) == [False, False, False]
    assert health.update(data(), 115) == [False, True, False]
    assert health.update(data(fps=[30, 30, 30]), 116) == [False, False, False]
    assert health.update(data(), 117) == [False, False, False]


@pytest.mark.parametrize(
    "changes",
    [
        {"running": False},
        {"status": "Calibrating"},
        {"status": "Starting"},
        {"cameras": False},
    ],
)
def test_normal_stop_calibration_and_standby_do_not_alarm(changes):
    health = CameraHealth()
    health.update(data(), 100)
    assert health.update(data(**changes), 130) == [False, False, False]
    assert health.update(data(), 131) == [False, False, False]


def test_unknown_fps_is_not_zero_and_interrupts_failure_window():
    health = CameraHealth()
    health.update(data(), 100)
    assert health.update(data(fps=[30, None, 30]), 120) == [False, None, False]
    assert health.update(data(), 121) == [False, False, False]
    assert health.update(data(fps=[]), 122) == [None, None, None]
