"""Tests for the /system/update/check endpoint."""

import subprocess
from unittest.mock import patch, MagicMock


def _mock_run(responses):
    """Build a subprocess.run side_effect from a list of (stdout, returncode) tuples."""
    calls = iter(responses)

    def side_effect(cmd, **kwargs):
        stdout, rc = next(calls)
        m = MagicMock()
        m.stdout = stdout
        m.stderr = ""
        m.returncode = rc
        return m

    return side_effect


def test_up_to_date(client):
    """When local and remote hashes match, reports no update."""
    responses = [
        ("", 0),                        # fetch
        ("main", 0),                    # rev-parse --abbrev-ref HEAD
        ("abc1234def5678", 0),          # rev-parse HEAD
        ("abc1234def5678", 0),          # rev-parse origin/main
    ]
    with patch("subprocess.run", side_effect=_mock_run(responses)), \
         patch("shutil.which", return_value="/usr/bin/git"):
        res = client.get("/system/update/check")
    assert res.status_code == 200
    data = res.get_json()
    assert data["available"] is False
    assert data["commits_behind"] == 0
    assert data["branch"] == "main"
    assert data["local_commit"] == "abc1234d"


def test_updates_available(client):
    """When remote is ahead, reports available updates with summary."""
    responses = [
        ("", 0),                        # fetch
        ("main", 0),                    # rev-parse --abbrev-ref HEAD
        ("aaa1111100000000", 0),        # rev-parse HEAD (local)
        ("bbb2222200000000", 0),        # rev-parse origin/main (remote)
        ("3", 0),                       # rev-list --count
        ("bbb2222 feat: new\nccc3333 fix: bug\nddd4444 chore: cleanup", 0),  # log
    ]
    with patch("subprocess.run", side_effect=_mock_run(responses)), \
         patch("shutil.which", return_value="/usr/bin/git"):
        res = client.get("/system/update/check")
    assert res.status_code == 200
    data = res.get_json()
    assert data["available"] is True
    assert data["commits_behind"] == 3
    assert data["local_commit"] == "aaa11111"
    assert data["remote_commit"] == "bbb22222"
    assert "feat: new" in data["summary"]


def test_remote_branch_not_found(client):
    """When origin/<branch> doesn't exist, returns error without crashing."""
    def side_effect(cmd, **kwargs):
        m = MagicMock()
        m.stderr = ""
        if "fetch" in cmd:
            m.stdout, m.returncode = "", 0
        elif cmd[-1] == "HEAD" and "--abbrev-ref" in cmd:
            m.stdout, m.returncode = "feature-x", 0
        elif cmd[-1] == "HEAD":
            m.stdout, m.returncode = "abc1234500000000", 0
        elif "origin/feature-x" in cmd:
            m.stdout, m.returncode = "", 1
            m.stderr = "unknown revision"
        else:
            m.stdout, m.returncode = "", 0
        return m

    with patch("subprocess.run", side_effect=side_effect), \
         patch("shutil.which", return_value="/usr/bin/git"):
        res = client.get("/system/update/check")
    assert res.status_code == 200
    data = res.get_json()
    assert data["available"] is False
    assert "not found" in data["error"]
    assert data["branch"] == "feature-x"


def test_timeout_no_internet(client):
    """When git fetch times out, returns graceful error."""
    def side_effect(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 15))

    with patch("subprocess.run", side_effect=side_effect), \
         patch("shutil.which", return_value="/usr/bin/git"):
        res = client.get("/system/update/check")
    assert res.status_code == 200
    data = res.get_json()
    assert data["available"] is False
    assert "Timed out" in data["error"]


def test_git_not_found(client):
    """When git binary is missing, returns 500."""
    with patch("shutil.which", return_value=None):
        res = client.get("/system/update/check")
    assert res.status_code == 500
