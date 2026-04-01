"""Tests for /stream_video and /sensor/test endpoints."""

import os
from unittest.mock import patch, MagicMock


def test_stream_video(client, rec_dir):
    path = os.path.join(rec_dir, "clip.mp4")
    with open(path, "wb") as f:
        f.write(b"\x00" * 128)

    res = client.get(f"/stream_video?video_path={path}")
    assert res.status_code == 200
    assert res.content_type.startswith("video/mp4")


def test_stream_video_missing(client):
    res = client.get("/stream_video?video_path=/nonexistent/video.mp4")
    assert res.status_code == 404


def test_stream_video_no_path(client):
    res = client.get("/stream_video")
    assert res.status_code == 404


def test_sensor_test_missing_type(client):
    res = client.post("/sensor/test", json={"gpio": 22})
    assert res.status_code == 400


def test_sensor_test_unknown_type(client):
    res = client.post("/sensor/test", json={"type": "nonexistent", "gpio": 22})
    assert res.status_code == 400


def test_sensor_test_mock_no_gpio(client):
    res = client.post("/sensor/test", json={"type": "mock"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["value"] is None
