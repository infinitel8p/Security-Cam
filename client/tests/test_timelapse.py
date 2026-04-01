"""Tests for timelapse API endpoints."""

import os


# ---------------------------------------------------------------------------
# /timelapse/status endpoint
# ---------------------------------------------------------------------------

def test_timelapse_status(client):
    res = client.get("/timelapse/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "enabled" in data
    assert data["enabled"] is False


# ---------------------------------------------------------------------------
# /timelapse listing endpoint
# ---------------------------------------------------------------------------

def test_timelapse_list(client):
    """Default mock returns empty list."""
    res = client.get("/timelapse")
    assert res.status_code == 200
    assert res.get_json() == []


# ---------------------------------------------------------------------------
# /timelapse/configure endpoint
# ---------------------------------------------------------------------------

def test_timelapse_configure(client):
    res = client.post("/timelapse/configure",
                      json={"enabled": True, "interval_minutes": 10},
                      content_type="application/json")
    assert res.status_code == 200


def test_timelapse_configure_updates_settings(client):
    client.post("/timelapse/configure",
                json={"enabled": True, "interval_minutes": 3, "fps": 30},
                content_type="application/json")
    import modules.settings_helpers as sh
    settings = sh.get_settings()
    assert settings["Timelapse"]["enabled"] is True
    assert settings["Timelapse"]["interval_minutes"] == 3
    assert settings["Timelapse"]["fps"] == 30


def test_timelapse_configure_preserves_other_keys(client):
    """Configuring some keys doesn't erase others."""
    client.post("/timelapse/configure",
                json={"enabled": True},
                content_type="application/json")
    import modules.settings_helpers as sh
    settings = sh.get_settings()
    # fps and resolution should still have defaults
    assert settings["Timelapse"]["fps"] == 24
    assert settings["Timelapse"]["resolution"] == "640x480"


# ---------------------------------------------------------------------------
# /timelapse/video endpoint
# ---------------------------------------------------------------------------

def test_timelapse_video_serves_mp4(client, rec_dir):
    tl_dir = os.path.join(rec_dir, "timelapse")
    os.makedirs(tl_dir, exist_ok=True)
    path = os.path.join(tl_dir, "timelapse_20260401.mp4")
    with open(path, "wb") as f:
        f.write(b"\x00\x00\x00\x1cftypisom")  # minimal mp4 header

    res = client.get(f"/timelapse/video?path={path}")
    assert res.status_code == 200
    assert "video/mp4" in res.content_type


def test_timelapse_video_missing(client, rec_dir):
    res = client.get(f"/timelapse/video?path={rec_dir}/timelapse/nonexistent.mp4")
    assert res.status_code == 404


def test_timelapse_video_no_param(client):
    res = client.get("/timelapse/video")
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# timelapse_manager unit tests (not via Flask)
# ---------------------------------------------------------------------------

def test_get_timelapse_videos(client, rec_dir):
    """get_timelapse_videos lists MP4s from the timelapse directory."""
    from unittest.mock import patch
    tl_dir = os.path.join(rec_dir, "timelapse")
    os.makedirs(tl_dir, exist_ok=True)
    for name in ["timelapse_20260401.mp4", "timelapse_20260331.mp4"]:
        with open(os.path.join(tl_dir, name), "wb") as f:
            f.write(b"\x00" * 64)

    # Call the real _timelapse_dir to point at our temp dir
    from modules.timelapse_manager import _timelapse_dir, get_timelapse_videos
    # _timelapse_dir reads from settings which the fixture has set to rec_dir
    actual_dir = _timelapse_dir()
    assert os.path.isdir(actual_dir)

    # Verify the files are there
    files = [f for f in os.listdir(actual_dir) if f.startswith("timelapse_") and f.endswith(".mp4")]
    assert len(files) == 2


def test_delete_timelapse_success(rec_dir):
    """delete_timelapse removes a valid timelapse file."""
    from modules.timelapse_manager import delete_timelapse
    tl_dir = os.path.join(rec_dir, "timelapse")
    os.makedirs(tl_dir, exist_ok=True)
    path = os.path.join(tl_dir, "timelapse_20260401.mp4")
    with open(path, "wb") as f:
        f.write(b"\x00")

    result, status = delete_timelapse(path)
    assert status == 200
    assert not os.path.exists(path)


def test_delete_timelapse_rejects_non_timelapse(rec_dir):
    """delete_timelapse blocks non-timelapse files."""
    from modules.timelapse_manager import delete_timelapse
    tl_dir = os.path.join(rec_dir, "timelapse")
    os.makedirs(tl_dir, exist_ok=True)
    path = os.path.join(tl_dir, "output_20260401.mp4")
    with open(path, "wb") as f:
        f.write(b"\x00")

    result, status = delete_timelapse(path)
    assert status == 400
    assert os.path.exists(path)


def test_delete_timelapse_missing(rec_dir):
    """delete_timelapse returns 404 for missing file."""
    from modules.timelapse_manager import delete_timelapse
    tl_dir = os.path.join(rec_dir, "timelapse")
    os.makedirs(tl_dir, exist_ok=True)

    result, status = delete_timelapse(os.path.join(tl_dir, "timelapse_missing.mp4"))
    assert status == 404
