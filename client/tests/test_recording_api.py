"""Tests for recording and stream settings endpoints."""

from datetime import datetime, timezone

import modules.stream_helpers as sh


def test_recording_status(client):
    res = client.get("/recording_status")
    assert res.status_code == 200
    data = res.get_json()
    assert "recording" in data
    assert data["recording"] is False
    assert "started_at" not in data


def test_recording_status_includes_started_at(client):
    """When recording is active, /recording_status includes started_at."""
    now = datetime.now(timezone.utc)
    sh.is_recording = True
    sh._recording_start_time = now
    try:
        res = client.get("/recording_status")
        assert res.status_code == 200
        data = res.get_json()
        assert data["recording"] is True
        assert data["started_at"] == now.isoformat()
    finally:
        sh.is_recording = False
        sh._recording_start_time = None


def test_toggle_recording_start(client):
    sh.is_recording = False
    res = client.post("/toggle_recording")
    assert res.status_code == 200
    assert "started" in res.get_json()["message"].lower()


def test_toggle_recording_stop(client):
    sh.is_recording = True
    try:
        res = client.post("/toggle_recording")
        assert res.status_code == 200
        assert "stopped" in res.get_json()["message"].lower()
    finally:
        sh.is_recording = False


def test_stream_settings_get(client):
    res = client.get("/stream_settings")
    assert res.status_code == 200
    data = res.get_json()
    assert data["width"] == 1296
    assert data["height"] == 972
    assert data["fps"] == 30


def test_stream_settings_post(client):
    res = client.post("/stream_settings", json={
        "width": 1920, "height": 1080, "fps": 15,
    })
    assert res.status_code == 200


def test_stream_settings_post_empty(client):
    res = client.post("/stream_settings", json={})
    assert res.status_code == 400
