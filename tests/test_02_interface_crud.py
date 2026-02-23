"""Tests for OPNsense Reticulum interface CRUD API."""

import pytest

pytestmark = pytest.mark.integration


def _selected_option(field):
    """Return the selected value from an OPNsense OptionField dict.

    OPNsense returns OptionFields as a dict of options:
      {"UDPInterface": {"value": "UDPInterface", "selected": 1}, ...}
    """
    if isinstance(field, dict):
        return next((k for k, v in field.items() if isinstance(v, dict) and v.get("selected")), None)
    return field  # plain string


def test_interface_full_lifecycle(api):
    """add → search → get → update → toggle → delete."""

    # Add
    data = api.add_interface({
        "enabled": "1",
        "name": "CI-Test-UDP",
        "interfaceType": "UDPInterface",
        "outgoing": "1",
        "udp_listen_port": "14200",
    })
    assert "uuid" in data, f"Expected uuid in response: {data}"
    uuid = data["uuid"]

    try:
        # Search — must appear in list
        rows = api.search_interfaces().get("rows", [])
        assert any(r.get("uuid") == uuid for r in rows), "New interface not in search results"

        # Get by UUID
        iface = api.get_interface(uuid).get("interface", {})
        assert iface.get("name") == "CI-Test-UDP"
        assert _selected_option(iface.get("interfaceType")) == "UDPInterface"

        # Update
        result = api.set_interface(uuid, {"name": "CI-Test-UDP-Updated", "udp_listen_port": "14201"})
        assert result.get("result") in ("saved", "OK")

        # Verify update persisted
        assert api.get_interface(uuid).get("interface", {}).get("name") == "CI-Test-UDP-Updated"

        # Toggle (disable)
        api.toggle_interface(uuid)

        # Toggle back (enable)
        api.toggle_interface(uuid)

    finally:
        api.del_interface(uuid)

    # Verify deleted
    rows = api.search_interfaces().get("rows", [])
    assert not any(r.get("uuid") == uuid for r in rows), "Interface still present after delete"
