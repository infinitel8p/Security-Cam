"""Tests for thumbnail serving and archive badge count endpoints."""

import json
import os
import time
from unittest.mock import patch


# ---------------------------------------------------------------------------
# /thumbnail endpoint tests
# ---------------------------------------------------------------------------


def test_thumbnail_returns_jpeg(client, tmp_path):
    thumb = tmp_path / "output_20260401_100000.thumb.jpg"
    thumb.write_bytes(b"\xff\xd8\xff\xe0JFIF")  # Minimal JPEG header

    res = client.get(f"/thumbnail?video_path={tmp_path}/output_20260401_100000.mp4")
    assert res.status_code == 200
    assert res.content_type.startswith("image/jpeg")


def test_thumbnail_missing(client, tmp_path):
    res = client.get(f"/thumbnail?video_path={tmp_path}/nonexistent.mp4")
    assert res.status_code == 404


def test_thumbnail_no_param(client):
    res = client.get("/thumbnail")
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# /archive/new_count endpoint tests
# ---------------------------------------------------------------------------


def test_archive_new_count_returns_count(client, rec_dir):
    from datetime import datetime, timezone, timedelta
    now = time.time()
    for i in range(3):
        path = os.path.join(rec_dir, f"output_20260401_10000{i}.mp4")
        with open(path, "w") as f:
            f.write("video data")
        os.utime(path, (now - i * 3600, now - i * 3600))

    # All 3 should be new since 4 hours ago
    since = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
    from urllib.parse import quote
    res = client.get(f"/archive/new_count?since={quote(since)}")
    assert res.status_code == 200
    assert res.get_json()["count"] == 3


def test_archive_new_count_filters_by_time(client, rec_dir):
    from datetime import datetime, timezone, timedelta
    now = time.time()

    old = os.path.join(rec_dir, "output_20260401_080000.mp4")
    with open(old, "w") as f:
        f.write("old")
    os.utime(old, (now - 7200, now - 7200))  # 2 hours ago

    new = os.path.join(rec_dir, "output_20260401_100000.mp4")
    with open(new, "w") as f:
        f.write("new")
    os.utime(new, (now - 60, now - 60))  # 1 min ago

    # Since 1 hour ago — only the recent one should count
    since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    from urllib.parse import quote
    res = client.get(f"/archive/new_count?since={quote(since)}")
    data = res.get_json()
    assert data["count"] == 1


def test_archive_new_count_no_since(client):
    res = client.get("/archive/new_count")
    assert res.status_code == 200
    assert res.get_json()["count"] == 0


def test_archive_new_count_invalid_since(client):
    res = client.get("/archive/new_count?since=not-a-date")
    assert res.status_code == 200
    assert res.get_json()["count"] == 0


def test_archive_new_count_excludes_tmp(client, rec_dir):
    now = time.time()

    real = os.path.join(rec_dir, "output_20260401_100000.mp4")
    with open(real, "w") as f:
        f.write("real")

    tmp = os.path.join(rec_dir, "output_20260401_100000.tmp.mp4")
    with open(tmp, "w") as f:
        f.write("tmp")

    res = client.get("/archive/new_count?since=2020-01-01T00:00:00%2B00:00")
    assert res.get_json()["count"] == 1


# ---------------------------------------------------------------------------
# Archive includes thumbnail path
# ---------------------------------------------------------------------------


def test_archive_includes_thumbnail(client, rec_dir):
    """Videos with .thumb.jpg sidecar include a thumbnail field."""
    video = os.path.join(rec_dir, "output_20260401_100000.mp4")
    thumb = os.path.join(rec_dir, "output_20260401_100000.thumb.jpg")
    with open(video, "w") as f:
        f.write("video data")
    with open(thumb, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0")

    res = client.get("/archive")
    data = res.get_json()
    assert len(data) == 1
    assert data[0]["thumbnail"] == thumb


def test_archive_no_thumbnail_field_when_missing(client, rec_dir):
    """Videos without a thumbnail don't have the field."""
    video = os.path.join(rec_dir, "output_20260401_100000.mp4")
    with open(video, "w") as f:
        f.write("video data")

    res = client.get("/archive")
    data = res.get_json()
    assert len(data) == 1
    assert "thumbnail" not in data[0]


def test_delete_removes_thumbnail(client, rec_dir):
    """Deleting a video also removes its thumbnail."""
    video = os.path.join(rec_dir, "output_20260401_100000.mp4")
    thumb = os.path.join(rec_dir, "output_20260401_100000.thumb.jpg")
    meta = os.path.join(rec_dir, "output_20260401_100000.meta.json")
    for path in (video, thumb):
        with open(path, "wb") as f:
            f.write(b"data")
    with open(meta, "w") as f:
        json.dump({"reason": "manual"}, f)

    res = client.post("/delete_video",
                      json={"video_path": video},
                      content_type="application/json")
    assert res.status_code == 200
    assert not os.path.exists(video)
    assert not os.path.exists(thumb)
    assert not os.path.exists(meta)
