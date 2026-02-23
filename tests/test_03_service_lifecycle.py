"""Tests for OPNsense Reticulum service lifecycle API."""

import time

import pytest

pytestmark = pytest.mark.integration


def _status(api):
    data = api.service_status()
    assert "status" in data, f"Missing 'status' key in response: {data}"
    return data


def test_service_status_endpoint(api):
    """Status endpoint returns a recognised state.

    'disabled' is valid when general.enabled=0 (plugin default on fresh install).
    'stopped'  = enabled in config but not running.
    'running'  = active.
    """
    data = _status(api)
    assert data["status"] in ("running", "stopped", "disabled")


def test_service_start(api):
    """Enabling the service and running reconfigure brings it up."""
    api.set_settings({"enabled": "1", "enable_transport": "0"})
    api.service_reconfigure()
    time.sleep(8)

    data = _status(api)
    assert data["status"] == "running", f"Service not running after reconfigure: {data}"
    assert data.get("rnsd") is True


def test_service_restart(api):
    """Restart keeps service running."""
    api.service_restart()
    time.sleep(8)

    assert _status(api)["status"] == "running"


def test_service_stop(api):
    """Stopping the service changes status to stopped."""
    api.service_stop()
    time.sleep(5)

    assert _status(api)["status"] == "stopped"


def test_service_reconfigure_restarts(api):
    """Reconfigure when enabled brings service back up."""
    api.service_reconfigure()
    time.sleep(8)

    assert _status(api)["status"] == "running"
