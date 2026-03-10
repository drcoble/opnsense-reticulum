"""Tests for OPNsense Reticulum service lifecycle API."""

import time


def _status(api):
    resp = api.get("/api/reticulum/service/status")
    assert resp.status_code == 200
    return resp.json()


def test_service_status_endpoint(api):
    """Status endpoint returns a recognised state.

    'disabled' is valid when general.enabled=0 (plugin default on fresh install).
    'stopped'  = enabled in config but not running.
    'running'  = active.
    """
    data = _status(api)
    assert "status" in data
    assert data["status"] in ("running", "stopped", "disabled")


def test_service_start(api):
    """Enabling the service and running reconfigure brings it up."""
    # saveContainerSettings('reticulum', 'general') expects flat fields under 'reticulum'
    api.post(
        "/api/reticulum/settings/set",
        json={"reticulum": {"enabled": "1", "enable_transport": "0"}},
    )

    resp = api.post("/api/reticulum/service/reconfigure")
    assert resp.status_code == 200
    time.sleep(8)

    data = _status(api)
    assert data["status"] == "running", f"Service not running after reconfigure: {data}"
    assert data.get("rnsd") is True


def test_service_restart(api):
    """Restart keeps service running."""
    resp = api.post("/api/reticulum/service/restart")
    assert resp.status_code == 200
    time.sleep(8)

    assert _status(api)["status"] == "running"


def test_service_stop(api):
    """Stopping the service changes status to stopped."""
    resp = api.post("/api/reticulum/service/stop")
    assert resp.status_code == 200
    time.sleep(5)

    assert _status(api)["status"] == "stopped"


def test_service_reconfigure_restarts(api):
    """Reconfigure when enabled brings service back up."""
    resp = api.post("/api/reticulum/service/reconfigure")
    assert resp.status_code == 200
    time.sleep(8)

    assert _status(api)["status"] == "running"
