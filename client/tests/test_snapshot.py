"""Tests for snapshot capture, listing, serving, and deletion."""

import os
from unittest.mock import patch, MagicMock


def test_snapshot_success(client, rec_dir):
    """POST /snapshot returns 200 with a path when ffmpeg succeeds."""
    def fake_run(cmd, **kwargs):
        # Create the output file ffmpeg would produce
        out_path = cmd[-1]
        with open(out_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0JFIF")
        return MagicMock(returncode=0, stderr=b"")

    with patch("modules.stream_helpers.subprocess.run", side_effect=fake_run):
        res = client.post("/snapshot")

    assert res.status_code == 200
    data = res.get_json()
    assert "path" in data
    assert data["path"].endswith(".jpg")
    assert os.path.exists(data["path"])


def test_snapshot_filename_pattern(client, rec_dir):
    """Snapshot filename matches snapshot_YYYYMMDD_HHMMSS.jpg."""
    def fake_run(cmd, **kwargs):
        out_path = cmd[-1]
        with open(out_path, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0JFIF")
        return MagicMock(returncode=0, stderr=b"")

    with patch("modules.stream_helpers.subprocess.run", side_effect=fake_run):
        res = client.post("/snapshot")

    import re
    filename = os.path.basename(res.get_json()["path"])
    assert re.match(r"snapshot_\d{8}_\d{6}\.jpg", filename)


def test_snapshot_ffmpeg_fails(client, rec_dir):
    """POST /snapshot returns 500 when ffmpeg produces no output."""
    def fake_run(cmd, **kwargs):
        # Don't create the file - simulates ffmpeg failure
        return MagicMock(returncode=1, stderr=b"error")

    with patch("modules.stream_helpers.subprocess.run", side_effect=fake_run):
        res = client.post("/snapshot")

    assert res.status_code == 500


def test_snapshot_ffmpeg_timeout(client, rec_dir):
    """POST /snapshot returns 500 when ffmpeg times out."""
    import subprocess

    with patch("modules.stream_helpers.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="ffmpeg", timeout=10)):
        res = client.post("/snapshot")

    assert res.status_code == 500


# ---------------------------------------------------------------------------
# /snapshots listing endpoint
# ---------------------------------------------------------------------------


def test_snapshots_list(client, rec_dir):
    """GET /snapshots returns snapshot files."""
    for name in ["snapshot_20260401_100000.jpg", "snapshot_20260401_110000.jpg"]:
        with open(os.path.join(rec_dir, name), "wb") as f:
            f.write(b"\xff\xd8\xff\xe0JFIF")

    res = client.get("/snapshots")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 2
    assert all("path" in s and "size" in s for s in data)


def test_snapshots_excludes_non_snapshots(client, rec_dir):
    """GET /snapshots ignores regular JPEGs and videos."""
    with open(os.path.join(rec_dir, "snapshot_20260401_100000.jpg"), "wb") as f:
        f.write(b"\xff\xd8")
    with open(os.path.join(rec_dir, "output_20260401_100000.thumb.jpg"), "wb") as f:
        f.write(b"\xff\xd8")
    with open(os.path.join(rec_dir, "output_20260401_100000.mp4"), "wb") as f:
        f.write(b"\x00")

    res = client.get("/snapshots")
    data = res.get_json()
    assert len(data) == 1
    assert "snapshot_" in data[0]["path"]


def test_snapshots_empty(client, rec_dir):
    """GET /snapshots returns empty list when no snapshots exist."""
    res = client.get("/snapshots")
    assert res.status_code == 200
    assert res.get_json() == []


# ---------------------------------------------------------------------------
# /snapshot_image serving endpoint
# ---------------------------------------------------------------------------


def test_snapshot_image_serves_jpeg(client, rec_dir):
    """GET /snapshot_image returns the JPEG file."""
    path = os.path.join(rec_dir, "snapshot_20260401_100000.jpg")
    with open(path, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0JFIF")

    res = client.get(f"/snapshot_image?path={path}")
    assert res.status_code == 200
    assert res.content_type.startswith("image/jpeg")


def test_snapshot_image_missing(client, rec_dir):
    """GET /snapshot_image returns 404 for missing file."""
    res = client.get(f"/snapshot_image?path={rec_dir}/nonexistent.jpg")
    assert res.status_code == 404


def test_snapshot_image_no_param(client):
    """GET /snapshot_image returns 400 without path param."""
    res = client.get("/snapshot_image")
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# /delete_snapshot endpoint
# ---------------------------------------------------------------------------


def test_delete_snapshot_success(client, rec_dir):
    """POST /delete_snapshot removes the file."""
    path = os.path.join(rec_dir, "snapshot_20260401_100000.jpg")
    with open(path, "wb") as f:
        f.write(b"\xff\xd8")

    res = client.post("/delete_snapshot",
                      json={"snapshot_path": path},
                      content_type="application/json")
    assert res.status_code == 200
    assert not os.path.exists(path)


def test_delete_snapshot_rejects_non_snapshot(client, rec_dir):
    """POST /delete_snapshot blocks deletion of non-snapshot files."""
    path = os.path.join(rec_dir, "output_20260401_100000.mp4")
    with open(path, "wb") as f:
        f.write(b"\x00")

    res = client.post("/delete_snapshot",
                      json={"snapshot_path": path},
                      content_type="application/json")
    assert res.status_code == 400
    assert os.path.exists(path)


def test_delete_snapshot_missing(client, rec_dir):
    """POST /delete_snapshot returns 404 for missing file."""
    res = client.post("/delete_snapshot",
                      json={"snapshot_path": os.path.join(rec_dir, "snapshot_missing.jpg")},
                      content_type="application/json")
    assert res.status_code == 404
