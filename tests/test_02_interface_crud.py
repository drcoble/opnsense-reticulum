"""Tests for OPNsense Reticulum interface CRUD API."""


def _selected_option(field):
    """Return the selected value from an OPNsense OptionField dict.

    OPNsense returns OptionFields as a dict of options:
      {"UDPInterface": {"value": "UDPInterface", "selected": 1}, ...}
    """
    if isinstance(field, dict):
        return next((k for k, v in field.items() if isinstance(v, dict) and v.get("selected")), None)
    return field  # plain string (older API behaviour)


def test_interface_full_lifecycle(api):
    """add → search → get → update → toggle → delete."""

    # Add
    resp = api.post(
        "/api/reticulum/settings/addInterface",
        json={
            "interface": {
                "enabled": "1",
                "name": "CI-Test-UDP",
                "interfaceType": "UDPInterface",
                "outgoing": "1",
                "udp_listen_port": "14200",
            }
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "uuid" in data, f"Expected uuid in response: {data}"
    uuid = data["uuid"]

    try:
        # Search — must appear in list
        resp = api.get("/api/reticulum/settings/searchInterface")
        assert resp.status_code == 200
        rows = resp.json().get("rows", [])
        assert any(r.get("uuid") == uuid for r in rows), "New interface not in search results"

        # Get by UUID
        resp = api.get(f"/api/reticulum/settings/getInterface/{uuid}")
        assert resp.status_code == 200
        iface = resp.json().get("interface", {})
        assert iface.get("name") == "CI-Test-UDP"
        # interfaceType is an OptionField — OPNsense returns a dict of options
        assert _selected_option(iface.get("interfaceType")) == "UDPInterface"

        # Update
        resp = api.post(
            f"/api/reticulum/settings/setInterface/{uuid}",
            json={"interface": {"name": "CI-Test-UDP-Updated", "udp_listen_port": "14201"}},
        )
        assert resp.status_code == 200
        assert resp.json().get("result") in ("saved", "OK")

        # Verify update persisted
        resp = api.get(f"/api/reticulum/settings/getInterface/{uuid}")
        assert resp.json().get("interface", {}).get("name") == "CI-Test-UDP-Updated"

        # Toggle (disable)
        resp = api.post(f"/api/reticulum/settings/toggleInterface/{uuid}")
        assert resp.status_code == 200

        # Toggle back (enable)
        resp = api.post(f"/api/reticulum/settings/toggleInterface/{uuid}")
        assert resp.status_code == 200

    finally:
        # Delete (always clean up)
        api.post(f"/api/reticulum/settings/delInterface/{uuid}")

    # Verify deleted
    resp = api.get("/api/reticulum/settings/searchInterface")
    rows = resp.json().get("rows", [])
    assert not any(r.get("uuid") == uuid for r in rows), "Interface still present after delete"
