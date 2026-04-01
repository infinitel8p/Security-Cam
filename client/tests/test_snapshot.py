"""Tests for the /snapshot endpoint."""

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
        # Don't create the file — simulates ffmpeg failure
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
