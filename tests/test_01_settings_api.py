"""Tests for OPNsense Reticulum settings API."""


def test_get_general_settings(api):
    """GET /settings/get returns 200 with a 'reticulum' key."""
    resp = api.get("/api/reticulum/settings/get")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "reticulum" in data


def test_set_general_settings(api):
    """POST /settings/set saves flat fields under the 'reticulum' key."""
    # saveContainerSettings('reticulum', 'general') does getPost('reticulum') then
    # calls setNodes() on the general node — so the body must be flat under 'reticulum',
    # not nested inside a 'general' sub-key.
    resp = api.post(
        "/api/reticulum/settings/set",
        json={"reticulum": {"enabled": "1", "enable_transport": "0", "loglevel": "1"}},
    )
    assert resp.status_code == 200
    assert resp.json().get("result") in ("saved", "OK")


def test_settings_persist(api):
    """enabled=1 set in test_set_general_settings survives a GET."""
    resp = api.get("/api/reticulum/settings/get")
    assert resp.status_code == 200
    data = resp.json()
    # getBase('reticulum', 'general') returns {"reticulum": {<general fields>}}
    general = data.get("reticulum", {})
    assert str(general.get("enabled", "")).strip() in ("1", "true")


def test_get_propagation_settings(api):
    """GET /settings/getPropagation returns 200 with a 'propagation' key."""
    resp = api.get("/api/reticulum/settings/getPropagation")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "propagation" in data


def test_set_propagation_settings(api):
    """POST /settings/setPropagation saves flat fields under the 'propagation' key."""
    # saveContainerSettings('propagation', 'propagation') does getPost('propagation')
    resp = api.post(
        "/api/reticulum/settings/setPropagation",
        json={"propagation": {"enabled": "0", "enable_node": "0"}},
    )
    assert resp.status_code == 200
    assert resp.json().get("result") in ("saved", "OK")
