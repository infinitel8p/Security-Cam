"""Tests for device management endpoints (BT + WiFi)."""


def test_add_bt_device(client):
    res = client.post("/devices/bt/add", json={
        "address": "AA:BB:CC:DD:EE:FF",
        "name": "Test Phone",
    })
    assert res.status_code == 200

    # Verify it's persisted in settings
    settings = client.get("/settings").get_json()
    bt = settings["TARGET_BT_ADDRESSES"]
    assert any(d["address"] == "AA:BB:CC:DD:EE:FF" for d in bt)


def test_add_bt_device_no_address(client):
    res = client.post("/devices/bt/add", json={"name": "Phone"})
    assert res.status_code == 400


def test_remove_bt_device(client):
    # Add then remove
    client.post("/devices/bt/add", json={
        "address": "11:22:33:44:55:66",
        "name": "Device",
    })
    res = client.post("/devices/bt/remove", json={
        "address": "11:22:33:44:55:66",
    })
    assert res.status_code == 200

    settings = client.get("/settings").get_json()
    bt = settings["TARGET_BT_ADDRESSES"]
    assert not any(d["address"] == "11:22:33:44:55:66" for d in bt)


def test_remove_bt_device_case_insensitive(client):
    client.post("/devices/bt/add", json={
        "address": "AA:BB:CC:DD:EE:FF",
        "name": "Phone",
    })
    res = client.post("/devices/bt/remove", json={
        "address": "aa:bb:cc:dd:ee:ff",
    })
    assert res.status_code == 200

    settings = client.get("/settings").get_json()
    assert len(settings["TARGET_BT_ADDRESSES"]) == 0


def test_add_bt_device_no_duplicate(client):
    for _ in range(3):
        client.post("/devices/bt/add", json={
            "address": "AA:BB:CC:DD:EE:FF",
            "name": "Phone",
        })

    settings = client.get("/settings").get_json()
    addrs = [d["address"] for d in settings["TARGET_BT_ADDRESSES"]]
    assert addrs.count("AA:BB:CC:DD:EE:FF") == 1


def test_add_wifi_device(client):
    res = client.post("/devices/wifi/add", json={
        "address": "00:11:22:33:44:55",
        "name": "Laptop",
    })
    assert res.status_code == 200

    settings = client.get("/settings").get_json()
    wifi = settings["TARGET_AP_MAC_ADDRESSES"]
    assert any(d["address"] == "00:11:22:33:44:55" for d in wifi)


def test_add_wifi_device_no_address(client):
    res = client.post("/devices/wifi/add", json={"name": "Laptop"})
    assert res.status_code == 400


def test_remove_wifi_device(client):
    client.post("/devices/wifi/add", json={
        "address": "AA:BB:CC:DD:EE:FF",
        "name": "AP Client",
    })
    res = client.post("/devices/wifi/remove", json={
        "address": "AA:BB:CC:DD:EE:FF",
    })
    assert res.status_code == 200

    settings = client.get("/settings").get_json()
    assert len(settings["TARGET_AP_MAC_ADDRESSES"]) == 0


def test_connections(client):
    res = client.get("/connections")
    assert res.status_code == 200
    data = res.get_json()
    assert "bluetooth" in data
    assert "wifi" in data
    assert "ap_clients" in data


def test_device_status(client):
    res = client.get("/devices/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "bt" in data
    assert "wifi" in data
