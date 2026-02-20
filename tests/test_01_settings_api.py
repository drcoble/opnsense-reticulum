"""Tests for OPNsense Reticulum settings API."""


def test_get_general_settings(api):
    resp = api.get("/api/reticulum/settings/get")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "reticulum" in data


def test_set_general_settings(api):
    resp = api.post(
        "/api/reticulum/settings/set",
        json={"reticulum": {"general": {"enabled": "1", "enable_transport": "0", "loglevel": "1"}}},
    )
    assert resp.status_code == 200
    assert resp.json().get("result") in ("saved", "OK")


def test_settings_persist(api):
    resp = api.get("/api/reticulum/settings/get")
    assert resp.status_code == 200
    data = resp.json()
    general = data.get("reticulum", {}).get("general", data.get("reticulum", {}))
    assert str(general.get("enabled", "")).strip() in ("1", "true")


def test_get_propagation_settings(api):
    resp = api.get("/api/reticulum/settings/getPropagation")
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)


def test_set_propagation_settings(api):
    resp = api.post(
        "/api/reticulum/settings/setPropagation",
        json={"reticulum": {"propagation": {"enabled": "0", "enable_node": "0"}}},
    )
    assert resp.status_code == 200
    assert resp.json().get("result") in ("saved", "OK")
