"""Tests for the /settings endpoints."""


def test_get_settings(client):
    res = client.get("/settings")
    assert res.status_code == 200
    data = res.get_json()
    assert "VideoSaveLocation" in data
    assert "RotationAngle" in data
    assert "StreamWidth" in data
    assert "Sensor" in data


def test_update_settings(client):
    res = client.post("/settings", json={"RotationAngle": 180})
    assert res.status_code == 200

    res = client.get("/settings")
    assert res.get_json()["RotationAngle"] == 180


def test_update_preserves_other_keys(client):
    res = client.get("/settings")
    original_fps = res.get_json()["StreamFPS"]

    client.post("/settings", json={"RotationAngle": 90})

    res = client.get("/settings")
    data = res.get_json()
    assert data["RotationAngle"] == 90
    assert data["StreamFPS"] == original_fps


def test_update_video_save_location_valid(client, rec_dir):
    res = client.post("/settings", json={"VideoSaveLocation": rec_dir})
    assert res.status_code == 200


def test_update_video_save_location_invalid(client):
    from unittest.mock import patch
    with patch("modules.settings_helpers.is_valid_directory", return_value=False):
        res = client.post("/settings", json={
            "VideoSaveLocation": "/some/invalid/path"
        })
    assert res.status_code == 400


def test_update_stream_params(client):
    res = client.post("/settings", json={
        "StreamWidth": 1920,
        "StreamHeight": 1080,
        "StreamFPS": 15,
    })
    assert res.status_code == 200

    res = client.get("/settings")
    data = res.get_json()
    assert data["StreamWidth"] == 1920
    assert data["StreamHeight"] == 1080
    assert data["StreamFPS"] == 15


def test_defaults_are_merged(client):
    """All keys from settings.defaults.json should be present."""
    res = client.get("/settings")
    data = res.get_json()
    expected_keys = [
        "TARGET_BT_ADDRESSES", "TARGET_AP_MAC_ADDRESSES",
        "VideoSaveLocation", "RotationAngle", "RotationMode",
        "StreamWidth", "StreamHeight", "StreamFPS",
        "StorageLimit", "Sensor",
    ]
    for key in expected_keys:
        assert key in data, f"Missing default key: {key}"
