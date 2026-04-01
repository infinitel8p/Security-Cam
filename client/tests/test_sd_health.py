"""Tests for SD card health in /system_info."""

from unittest.mock import patch


def test_system_info_includes_sd_health(client):
    mock_sd = {
        "name": "SA16G",
        "serial": "0x12345678",
        "written_since_boot_gb": 42.5,
    }
    with patch("modules.system_helpers.get_cpu_temp", return_value=45.0), \
         patch("modules.system_helpers.get_cpu_load", return_value=10), \
         patch("modules.system_helpers.get_storage_info", return_value={}), \
         patch("modules.system_helpers.get_ram_usage", return_value={}), \
         patch("modules.system_helpers.get_uptime", return_value=3600), \
         patch("modules.system_helpers.get_throttle_status", return_value=None), \
         patch("modules.system_helpers.get_sd_health", return_value=mock_sd):

        res = client.get("/system_info")
        assert res.status_code == 200
        data = res.get_json()
        assert data["sd_health"] == mock_sd


def test_system_info_sd_health_null_on_non_pi(client):
    with patch("modules.system_helpers.get_cpu_temp", return_value=None), \
         patch("modules.system_helpers.get_cpu_load", return_value=0), \
         patch("modules.system_helpers.get_storage_info", return_value={}), \
         patch("modules.system_helpers.get_ram_usage", return_value={}), \
         patch("modules.system_helpers.get_uptime", return_value=0), \
         patch("modules.system_helpers.get_throttle_status", return_value=None), \
         patch("modules.system_helpers.get_sd_health", return_value=None):

        res = client.get("/system_info")
        assert res.status_code == 200
        assert res.get_json()["sd_health"] is None
