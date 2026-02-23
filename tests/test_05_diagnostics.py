"""Tests for OPNsense Reticulum diagnostics API endpoints."""

import time

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", autouse=True)
def service_running(api):
    """Ensure Reticulum is running before diagnostics tests, stop after."""
    api.set_settings({"enabled": "1"})
    api.service_reconfigure()
    time.sleep(10)

    status = api.service_status()
    if status.get("status") != "running":
        pytest.skip(f"Service not running, skipping diagnostics: {status}")

    yield

    api.service_stop()
    time.sleep(3)


def test_rnstatus(api):
    resp = api.diag_rnstatus()
    assert resp.get("status") == "ok"
    assert "data" in resp


def test_paths(api):
    resp = api.diag_paths()
    assert resp.get("status") == "ok"


def test_announces(api):
    resp = api.diag_announces()
    assert resp.get("status") == "ok"


def test_interfaces_diagnostics(api):
    resp = api.diag_interfaces()
    assert resp.get("status") == "ok"


def test_log_endpoint(api):
    resp = api.diag_log()
    assert resp.get("status") == "ok"
    data = resp.get("data", {})
    assert "lines" in data or "message" in data or "raw" in data
