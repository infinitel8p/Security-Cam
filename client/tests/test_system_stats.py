"""Tests for the /system_stats extended stats endpoint."""

from unittest.mock import patch, MagicMock


def test_system_stats(client):
    """GET /system_stats returns extended system information."""
    mock_net = MagicMock()
    mock_net.bytes_sent = 123456
    mock_net.bytes_recv = 654321
    mock_net.packets_sent = 100
    mock_net.packets_recv = 200

    mock_swap = MagicMock()
    mock_swap.total = 100 * 1024 ** 2
    mock_swap.used = 20 * 1024 ** 2
    mock_swap.percent = 20.0

    # Mock network interface addresses
    mock_addr = MagicMock()
    mock_addr.family.name = "AF_INET"
    mock_addr.address = "192.168.1.42"

    with patch("modules.system_helpers.psutil") as mock_psutil, \
         patch("socket.gethostname", return_value="raspberrypi"), \
         patch("getpass.getuser", return_value="pi"):
        mock_psutil.pids.return_value = list(range(85))
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_percent.return_value = [12.0, 8.0, 15.0, 5.0]
        mock_psutil.boot_time.return_value = 1743500000.0
        mock_psutil.net_io_counters.return_value = mock_net
        mock_psutil.swap_memory.return_value = mock_swap
        mock_psutil.getloadavg.return_value = (0.5, 0.3, 0.2)
        mock_psutil.net_if_addrs.return_value = {"wlan0": [mock_addr]}

        res = client.get("/system_stats")
        assert res.status_code == 200
        data = res.get_json()

        assert data["process_count"] == 85
        assert data["cpu_count"] == 4
        assert data["cpu_per_core"] == [12, 8, 15, 5]
        assert data["hostname"] == "raspberrypi"
        assert "boot_time" in data
        assert data["network"]["bytes_sent"] == 123456
        assert data["network"]["bytes_recv"] == 654321
        assert data["swap"]["total_mb"] == 100
        assert data["swap"]["used_mb"] == 20
        assert data["load_avg"]["1min"] == 0.5

        # Identity and platform info
        assert data["username"] == "pi"
        assert "python_version" in data
        assert "os_info" in data
        assert "arch" in data
        assert "kernel" in data
        assert "flask_version" in data
        assert data["ip_address"] == "192.168.1.42"
        assert data["ip_interface"] == "wlan0"
