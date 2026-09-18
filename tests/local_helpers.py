"""Synthetic fixtures shaped like Board Manager 1.0.7 responses."""

from copy import deepcopy

BASE = "http://192.0.2.10:3180"
STATE = {
    "connected": True,
    "running": False,
    "status": "Stopped",
    "event": "Stopped",
    "numThrows": 0,
}
CONFIG = {
    "auth": {"board_id": "board-1", "api_key": "private-board-api-key"},
    "cam": {
        "cams": ["/dev/video0", "/dev/video2", "/dev/video4"],
        "width": 1280,
        "height": 1024,
        "fps": 30,
        "auto_calibrate_on_start": True,
        "auto_calibrate": True,
        "auto_distortion": False,
    },
    "motion": {"standby_minutes": 15, "sensitive_calibration_setting": 123},
}


def mock_board(mock, *, state=None, config=None, config_status=200):
    mock.get(f"{BASE}/api/state", json=deepcopy(STATE if state is None else state))
    mock.get(
        f"{BASE}/api/config",
        json=deepcopy(CONFIG if config is None else config),
        status=config_status,
    )
    mock.get(f"{BASE}/api/version", text="1.0.7")
    mock.get(f"{BASE}/api/state/stats", json={"fps": 12.5})
    mock.get(f"{BASE}/api/cams/stats", json={"fps": [29.9, 30, 29.8]})
    mock.get(f"{BASE}/api/cams/state", json={"isRunning": False, "isOpened": False})
    mock.get(
        f"{BASE}/api/state/motion",
        json={
            "isStable": True,
            "isHand": False,
            "isTakeoutPartial": False,
            "isTakeoutFull": False,
        },
    )


def local_entry_data():
    return {
        "board_id": "board-1",
        "host": "192.0.2.10",
        "port": 3180,
        "local_only": True,
    }
