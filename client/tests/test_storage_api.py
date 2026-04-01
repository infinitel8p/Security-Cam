"""Tests for storage management endpoints."""


def test_storage_status(client):
    res = client.get("/storage/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "disk_percent" in data


def test_storage_configure(client):
    res = client.post("/storage/configure", json={
        "enabled": True,
        "max_percent": 75,
    })
    assert res.status_code == 200

    settings = client.get("/settings").get_json()
    cfg = settings["StorageLimit"]
    assert cfg["enabled"] is True
    assert cfg["max_percent"] == 75


def test_storage_configure_clamps_percent(client):
    # Below minimum
    client.post("/storage/configure", json={"max_percent": 1})
    settings = client.get("/settings").get_json()
    assert settings["StorageLimit"]["max_percent"] == 10

    # Above maximum
    client.post("/storage/configure", json={"max_percent": 100})
    settings = client.get("/settings").get_json()
    assert settings["StorageLimit"]["max_percent"] == 95


def test_storage_cleanup(client):
    res = client.post("/storage/cleanup")
    assert res.status_code == 200
    data = res.get_json()
    assert "action" in data
