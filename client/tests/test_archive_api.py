"""Tests for the /archive and /delete_video endpoints."""

import json
import os


def _create_video(rec_dir, name="output_2026-01-01_12-00-00.mp4", meta=None):
    """Helper to create a fake video file and optional sidecar metadata."""
    path = os.path.join(rec_dir, name)
    with open(path, "wb") as f:
        f.write(b"\x00" * 64)  # dummy content
    if meta:
        meta_path = os.path.splitext(path)[0] + ".meta.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f)
    return path


def test_archive_empty(client):
    res = client.get("/archive")
    assert res.status_code == 200
    assert res.get_json() == []


def test_archive_lists_videos(client, rec_dir):
    _create_video(rec_dir, "vid1.mp4")
    _create_video(rec_dir, "vid2.mp4")

    res = client.get("/archive")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 2


def test_archive_excludes_tmp_files(client, rec_dir):
    _create_video(rec_dir, "recording.mp4")
    _create_video(rec_dir, "recording.tmp.mp4")

    res = client.get("/archive")
    data = res.get_json()
    assert len(data) == 1
    assert not data[0]["path"].endswith(".tmp.mp4")


def test_archive_includes_metadata(client, rec_dir):
    _create_video(rec_dir, "event.mp4", meta={"trigger": "sensor"})

    res = client.get("/archive")
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["meta"]["trigger"] == "sensor"


def test_delete_video(client, rec_dir):
    path = _create_video(rec_dir)

    res = client.post("/delete_video", json={"video_path": path})
    assert res.status_code == 200
    assert not os.path.exists(path)


def test_delete_video_removes_sidecar(client, rec_dir):
    path = _create_video(rec_dir, "clip.mp4", meta={"source": "pir"})
    meta_path = os.path.splitext(path)[0] + ".meta.json"
    assert os.path.exists(meta_path)

    client.post("/delete_video", json={"video_path": path})
    assert not os.path.exists(path)
    assert not os.path.exists(meta_path)


def test_delete_video_missing(client, rec_dir):
    res = client.post("/delete_video", json={
        "video_path": os.path.join(rec_dir, "nonexistent.mp4")
    })
    assert res.status_code == 404


def test_delete_video_path_traversal(client, rec_dir):
    """Attempting to delete a file outside VideoSaveLocation should fail."""
    # Create a file outside the recordings dir
    import tempfile
    outside = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    outside.write(b"\x00" * 64)
    outside.close()

    try:
        res = client.post("/delete_video", json={
            "video_path": outside.name
        })
        assert res.status_code == 400
        assert os.path.exists(outside.name)  # file should NOT be deleted
    finally:
        os.unlink(outside.name)


def test_delete_rejects_non_mp4(client, rec_dir):
    path = os.path.join(rec_dir, "notes.txt")
    with open(path, "w") as f:
        f.write("not a video")

    res = client.post("/delete_video", json={"video_path": path})
    assert res.status_code == 400


def test_delete_rejects_tmp_mp4(client, rec_dir):
    path = _create_video(rec_dir, "recording.tmp.mp4")

    res = client.post("/delete_video", json={"video_path": path})
    assert res.status_code == 400
