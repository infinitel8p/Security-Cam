"""Tests for BT scan, WiFi stations, and BT discoverable endpoints."""

from unittest.mock import patch


def test_bt_scan(client):
    mock_devices = [
        {"address": "AA:BB:CC:DD:EE:FF", "name": "Phone"},
        {"address": "11:22:33:44:55:66", "name": "Laptop"},
    ]
    with patch("modules.activity_helpers.scan_bt_devices", return_value=mock_devices):
        res = client.post("/bt/scan")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["devices"]) == 2


def test_bt_scan_empty(client):
    with patch("modules.activity_helpers.scan_bt_devices", return_value=[]):
        res = client.post("/bt/scan")
    assert res.status_code == 200
    assert res.get_json()["devices"] == []


def test_bt_scan_error(client):
    with patch("modules.activity_helpers.scan_bt_devices",
               side_effect=RuntimeError("Bluetooth unavailable")):
        res = client.post("/bt/scan")
    assert res.status_code == 500
    assert "error" in res.get_json()


def test_wifi_stations(client):
    mock_stations = [{"address": "AA:BB:CC:DD:EE:FF", "name": "Phone"}]
    with patch("modules.activity_helpers.get_ap_stations", return_value=mock_stations), \
         patch("modules.activity_helpers.is_in_ap_mode", return_value=True):
        res = client.get("/wifi/stations")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["stations"]) == 1
    assert "message" not in data  # no "not in AP mode" message


def test_wifi_stations_not_ap_mode(client):
    with patch("modules.activity_helpers.get_ap_stations", return_value=[]), \
         patch("modules.activity_helpers.is_in_ap_mode", return_value=False):
        res = client.get("/wifi/stations")
    assert res.status_code == 200
    assert "message" in res.get_json()


def test_bt_discoverable_success(client):
    mock_device = {"address": "AA:BB:CC:DD:EE:FF", "name": "Phone"}
    with patch("modules.settings_helpers.make_bt_discoverable", return_value=mock_device):
        res = client.post("/bt/discoverable", json={"timeout": 30})
    assert res.status_code == 200
    data = res.get_json()
    assert data["device"]["address"] == "AA:BB:CC:DD:EE:FF"


def test_bt_discoverable_timeout(client):
    with patch("modules.settings_helpers.make_bt_discoverable",
               side_effect=RuntimeError("No device paired within the time limit")):
        res = client.post("/bt/discoverable", json={"timeout": 5})
    assert res.status_code == 408


def test_bt_discoverable_auto_registers(client):
    mock_device = {"address": "FF:EE:DD:CC:BB:AA", "name": "Tablet"}
    with patch("modules.settings_helpers.make_bt_discoverable", return_value=mock_device):
        client.post("/bt/discoverable", json={"timeout": 30})

    settings = client.get("/settings").get_json()
    bt = settings["TARGET_BT_ADDRESSES"]
    assert any(d["address"] == "FF:EE:DD:CC:BB:AA" for d in bt)
