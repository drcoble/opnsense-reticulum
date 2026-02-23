"""Test 02: Settings API round-trip and validation.

Tests GET/SET operations for general and propagation settings,
including round-trip consistency and invalid input rejection.
"""

import pytest

pytestmark = pytest.mark.integration


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
        assert resp["reticulum"]["loglevel"] == "7"

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


class TestPropagationSettings:
    """Propagation settings GET/SET round-trip tests."""

    def test_get_defaults(self, api):
        """GET returns default propagation settings."""
        resp = api.get_propagation()
        assert "propagation" in resp
        prop = resp["propagation"]
        assert "enabled" in prop
        assert "message_storage_limit" in prop

    def test_enable_propagation(self, api):
        """Enable propagation node."""
        result = api.set_propagation({"enabled": "1"})
        assert result.get("result") == "saved"

        resp = api.get_propagation()
        assert resp["propagation"]["enabled"] == "1"

    def test_set_storage_limit(self, api):
        """Set message_storage_limit."""
        result = api.set_propagation({"message_storage_limit": "5000"})
        assert result.get("result") == "saved"

        resp = api.get_propagation()
        assert resp["propagation"]["message_storage_limit"] == "5000"

    def test_set_sync_interval(self, api):
        """Set periodic_sync_interval."""
        result = api.set_propagation({"periodic_sync_interval": "600"})
        assert result.get("result") == "saved"

        resp = api.get_propagation()
        assert resp["propagation"]["periodic_sync_interval"] == "600"

    def test_invalid_sync_interval_rejected(self, api):
        """Sync interval below minimum (10) is rejected."""
        result = api.set_propagation({"periodic_sync_interval": "1"})
        assert "validations" in result or result.get("result") == "failed"
