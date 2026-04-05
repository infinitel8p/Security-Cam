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


def test_export_settings(client):
    """GET /settings/export returns a downloadable JSON file."""
    res = client.get("/settings/export")
    assert res.status_code == 200
    assert "attachment" in res.headers.get("Content-Disposition", "")
    data = res.get_json()
    assert "VideoSaveLocation" in data
    assert "RotationAngle" in data
    # Export includes auth fields (full backup)
    assert "Auth" in data


def test_import_settings(client):
    """POST /settings/import writes settings and returns success."""
    payload = {"RotationAngle": 270, "StreamFPS": 15}
    res = client.post("/settings/import", json=payload)
    assert res.status_code == 200

    res = client.get("/settings")
    data = res.get_json()
    assert data["RotationAngle"] == 270
    assert data["StreamFPS"] == 15


def test_import_preserves_unmentioned_keys(client):
    """Importing a partial set of keys should not remove existing keys."""
    res = client.get("/settings")
    original = res.get_json()

    client.post("/settings/import", json={"RotationAngle": 90})

    res = client.get("/settings")
    data = res.get_json()
    assert data["RotationAngle"] == 90
    assert data["VideoSaveLocation"] == original["VideoSaveLocation"]


def test_import_rejects_unknown_keys(client):
    """Importing settings with unknown keys should fail."""
    res = client.post("/settings/import", json={"UnknownKey": "value"})
    assert res.status_code == 400
    assert "Unknown" in res.get_json()["error"]


def test_import_rejects_non_dict(client):
    """Importing a non-dict JSON value should fail."""
    res = client.post("/settings/import",
                      data="[1,2,3]",
                      content_type="application/json")
    assert res.status_code == 400


def test_import_rejects_non_json(client):
    """Importing non-JSON content should fail."""
    res = client.post("/settings/import",
                      data="not json",
                      content_type="text/plain")
    assert res.status_code == 400


def test_import_rejects_oversized_payload(client):
    """Importing a payload larger than 256 KB should fail."""
    big = {"RotationAngle": 0, "VideoSaveLocation": "x" * (256 * 1024)}
    res = client.post("/settings/import", json=big)
    assert res.status_code == 413


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
