"""Tests for /list_directories endpoint."""

import os


def test_list_directories_valid(client, rec_dir):
    # Create some subdirs
    os.makedirs(os.path.join(rec_dir, "subdir1"))
    os.makedirs(os.path.join(rec_dir, "subdir2"))

    res = client.get(f"/list_directories?path={rec_dir}")
    assert res.status_code == 200
    data = res.get_json()
    assert "directories" in data
    assert len(data["directories"]) >= 2


def test_list_directories_invalid_path(client):
    res = client.get("/list_directories?path=/dev/null/nope")
    assert res.status_code == 400


def test_list_directories_default_path(client):
    res = client.get("/list_directories")
    # Default "./" should be valid since cwd exists
    assert res.status_code == 200
