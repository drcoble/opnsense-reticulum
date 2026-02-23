"""Test 02: Settings API round-trip and validation."""

import pytest

pytestmark = pytest.mark.integration


def _selected_dropdown(field):
    """Extract the selected value from an OPNsense OptionField.

    OPNsense returns OptionFields as a list of dicts like:
      [{"selected": 0, "value": "0 - None"}, {"selected": 1, "value": "7 - Debug"}, ...]
    Falls back to str(field) for plain values.
    """
    if isinstance(field, list):
        for item in field:
            if isinstance(item, dict) and item.get("selected"):
                return item.get("value", "")
    return str(field) if field is not None else ""


class TestGeneralSettings:
    """General settings GET/SET round-trip tests."""

    def test_get_defaults(self, api):
        """GET returns default general settings."""
        resp = api.get_settings()
        assert "reticulum" in resp
        general = resp["reticulum"]
        assert "enabled" in general
        assert "loglevel" in general

    def test_enable_plugin(self, api):
        """SET enabled=1, GET confirms round-trip."""
        result = api.set_settings({"enabled": "1"})
        assert result.get("result") == "saved"

        resp = api.get_settings()
        assert resp["reticulum"]["enabled"] == "1"

    def test_set_loglevel(self, api):
        """SET loglevel to Debug (7), GET confirms."""
        result = api.set_settings({"loglevel": "7"})
        assert result.get("result") == "saved"

        resp = api.get_settings()
        loglevel = _selected_dropdown(resp["reticulum"]["loglevel"])
        assert "7" in loglevel, f"Expected loglevel containing '7', got: {loglevel}"

    def test_set_transport_enabled(self, api):
        """Enable transport mode."""
        result = api.set_settings({"enable_transport": "1"})
        assert result.get("result") == "saved"

        resp = api.get_settings()
        assert resp["reticulum"]["enable_transport"] == "1"

    def test_set_ports(self, api):
        """Set shared_instance_port and instance_control_port."""
        result = api.set_settings({
            "shared_instance_port": "37430",
            "instance_control_port": "37431",
        })
        assert result.get("result") == "saved"

        resp = api.get_settings()
        assert resp["reticulum"]["shared_instance_port"] == "37430"
        assert resp["reticulum"]["instance_control_port"] == "37431"

    def test_invalid_port_rejected(self, api):
        """POST invalid port value returns validation error."""
        result = api.set_settings({"shared_instance_port": "99999"})
        assert "validations" in result or result.get("result") == "failed"
