"""Tests for system info and monitoring endpoints."""

from unittest.mock import patch


def test_system_info(client):
    with patch("modules.system_helpers.get_cpu_temp", return_value=45.0), \
         patch("modules.system_helpers.get_cpu_load", return_value=12.5), \
         patch("modules.system_helpers.get_storage_info", return_value={
             "total": 16.0, "used": 6.7, "free": 9.3,
         }), \
         patch("modules.system_helpers.get_ram_usage", return_value={
             "total": 512, "used": 210, "percent": 41.0,
         }), \
         patch("modules.system_helpers.get_uptime", return_value=86400), \
         patch("modules.system_helpers.get_throttle_status", return_value=None):

        res = client.get("/system_info")
        assert res.status_code == 200
        data = res.get_json()
        assert data["cpu_temp_celsius"] == 45.0
        assert data["cpu_load_percent"] == 12.5
        assert data["uptime_seconds"] == 86400


def test_health_history(client):
    res = client.get("/health_history?hours=24")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_health_history_clamps_hours(client):
    # Max 72h
    res = client.get("/health_history?hours=9999")
    assert res.status_code == 200


def test_event_history(client):
    res = client.get("/event_history?hours=24")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_deploy_info(client):
    """deploy_info returns git branch and commit when inside a git repo."""
    res = client.get("/deploy_info")
    assert res.status_code == 200
    data = res.get_json()
    assert "git_branch" in data
    assert "git_commit" in data
    # Running inside the repo, so both should be populated
    assert isinstance(data["git_branch"], str)
    assert isinstance(data["git_commit"], str)


def test_deploy_info_included_in_extended_stats(client):
    """git info should also appear in /system_stats (via _get_static_info)."""
    res = client.get("/system_stats")
    assert res.status_code == 200
    data = res.get_json()
    assert "git_branch" in data
    assert "git_commit" in data
