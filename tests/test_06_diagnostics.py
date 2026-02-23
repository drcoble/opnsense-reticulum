"""Test 06: Diagnostics API endpoints.

Verifies diagnostics endpoints return valid JSON with expected structure.
Service must be running for meaningful results, but endpoints should return
valid JSON even when stopped.
"""

import time

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True, scope="module")
def ensure_service_running(request):
    """Start the service so diagnostics have data to report."""
    api = request.getfixturevalue("api")

    api.set_settings({"enabled": "1"})

    result = api.add_interface({
        "name": "CI Diag Test Auto",
        "interfaceType": "AutoInterface",
        "enabled": "1",
        "auto_group_id": "ci-diag-test",
    })
    uuid = result.get("uuid")

    api.service_reconfigure()
    time.sleep(3)
    api.service_start()
    time.sleep(5)

    yield uuid

    try:
        api.service_stop()
    except Exception:
        pass
    time.sleep(2)
    if uuid:
        try:
            api.del_interface(uuid)
        except Exception:
            pass
    api.set_settings({"enabled": "0"})


class TestDiagnostics:
    """Diagnostics endpoints return valid JSON."""

    def test_rnstatus(self, api):
        """GET /api/reticulum/diagnostics/rnstatus returns valid JSON."""
        resp = api.diag_rnstatus()
        assert resp.get("status") == "ok"
        assert "data" in resp

    def test_paths(self, api):
        """GET /api/reticulum/diagnostics/paths returns valid JSON."""
        resp = api.diag_paths()
        assert resp.get("status") == "ok"
        assert "data" in resp

    def test_announces(self, api):
        """GET /api/reticulum/diagnostics/announces returns valid JSON."""
        resp = api.diag_announces()
        assert resp.get("status") == "ok"
        assert "data" in resp

    def test_interfaces(self, api):
        """GET /api/reticulum/diagnostics/interfaces returns valid JSON."""
        resp = api.diag_interfaces()
        assert resp.get("status") == "ok"
        assert "data" in resp

    def test_log(self, api):
        """GET /api/reticulum/diagnostics/log returns valid JSON."""
        resp = api.diag_log()
        assert resp.get("status") == "ok"
        assert "data" in resp
        data = resp["data"]
        assert "lines" in data or "message" in data or "raw" in data
