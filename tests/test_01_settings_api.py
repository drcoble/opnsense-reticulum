"""Tests for OPNsense Reticulum settings API."""

import pytest

pytestmark = pytest.mark.integration


def test_get_general_settings(api):
    """GET /settings/get returns a dict with a 'reticulum' key."""
    data = api.get_settings()
    assert isinstance(data, dict)
    assert "reticulum" in data


def test_set_general_settings(api):
    """POST /settings/set saves flat fields under the 'reticulum' key."""
    result = api.set_settings({"enabled": "1", "enable_transport": "0", "loglevel": "1"})
    assert isinstance(result, dict)
    assert result.get("result") in ("saved", "OK")


def test_settings_persist(api):
    """enabled=1 set in test_set_general_settings survives a GET."""
    data = api.get_settings()
    general = data.get("reticulum", {})
    assert str(general.get("enabled", "")).strip() in ("1", "true")
