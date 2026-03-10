"""Tests for OPNsense Reticulum diagnostics API endpoints."""

import time
import pytest


@pytest.fixture(scope="module", autouse=True)
def service_running(api):
    """Ensure Reticulum is running before diagnostics tests, stop after."""
    # saveContainerSettings('reticulum', 'general') expects flat fields under 'reticulum'
    api.post(
        "/api/reticulum/settings/set",
        json={"reticulum": {"enabled": "1"}},
    )
    api.post("/api/reticulum/service/reconfigure")
    time.sleep(10)

    status = api.get("/api/reticulum/service/status").json()
    if status.get("status") != "running":
        pytest.skip(f"Service not running, skipping diagnostics: {status}")

    yield

    api.post("/api/reticulum/service/stop")
    time.sleep(3)


def test_rnstatus(api):
    resp = api.get("/api/reticulum/diagnostics/rnstatus")
    assert resp.status_code == 200
    assert len(resp.text) > 0


def test_paths(api):
    resp = api.get("/api/reticulum/diagnostics/paths")
    assert resp.status_code == 200


def test_announces(api):
    resp = api.get("/api/reticulum/diagnostics/announces")
    assert resp.status_code == 200


def test_interfaces_diagnostics(api):
    resp = api.get("/api/reticulum/diagnostics/interfaces")
    assert resp.status_code == 200


def test_propagation_diagnostics(api):
    resp = api.get("/api/reticulum/diagnostics/propagation")
    assert resp.status_code == 200
    outer = resp.json()
    # diagnostics endpoints return {"status": "ok", "data": {...}}
    assert "data" in outer
    data = outer["data"]
    assert "running" in data
    assert isinstance(data["running"], bool)
    assert "message_count" in data


def test_log_endpoint(api):
    resp = api.get("/api/reticulum/diagnostics/log")
    assert resp.status_code == 200
    assert isinstance(resp.text, str)
