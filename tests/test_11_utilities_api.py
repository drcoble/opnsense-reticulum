"""Test 11: Utilities API endpoints.

Tests all seven /api/reticulum/utilities/* endpoints including input
validation, output structure, and error handling. Requires rnsd to be
running so the CLI tools can connect to the local Reticulum instance.
"""

import time

import pytest

pytestmark = pytest.mark.integration

# A syntactically valid but almost certainly unknown hash for error-path tests
UNKNOWN_HASH = "deadbeef" * 4  # 32 hex chars


@pytest.fixture(autouse=True, scope="module")
def ensure_rnsd_running(request):
    """Enable plugin with an AutoInterface and start rnsd before utility tests."""
    api = request.getfixturevalue("api")

    api.set_settings({"enabled": "1"})
    result = api.add_interface({
        "name": "CI Utilities Test",
        "interfaceType": "AutoInterface",
        "enabled": "1",
        "auto_group_id": "ci-utilities",
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


class TestUtilitiesAPI:
    """Utilities API endpoint correctness tests."""

    def test_rnstatus_basic(self, api):
        """POST rnstatus (no detail) returns ok with non-empty output."""
        resp = api.util_rnstatus(detail=0)
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"
        data = resp.get("data", {})
        output = data.get("output") or data.get("raw") or ""
        assert output, f"rnstatus returned empty output: {resp}"

    def test_rnstatus_detail(self, api):
        """POST rnstatus with detail=1 returns more verbose output."""
        basic = api.util_rnstatus(detail=0)
        detailed = api.util_rnstatus(detail=1)

        assert detailed.get("status") == "ok"
        basic_out = str(basic.get("data", {}))
        detail_out = str(detailed.get("data", {}))
        # Detailed output should be at least as long
        assert len(detail_out) >= len(basic_out)

    def test_rnid_local_identity(self, api):
        """POST rnid with no hash returns local identity info."""
        resp = api.util_rnid()
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"
        data = resp.get("data", {})
        output = data.get("output") or data.get("raw") or ""
        assert output, "rnid returned empty output"

    def test_rnid_with_invalid_hash_no_crash(self, api):
        """POST rnid with an invalid hash does not crash the server."""
        resp = api.util_rnid(hash="not-a-valid-hash!!!")
        # Should return either an error status or a response without crashing
        assert resp is not None
        assert "status" in resp

    def test_rnid_unknown_hash_returns_ok(self, api):
        """POST rnid with a valid but unknown hash returns ok (not a server error)."""
        resp = api.util_rnid(hash=UNKNOWN_HASH)
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"

    def test_rnpath_missing_hash_returns_error(self, api):
        """POST rnpath with no hash returns status=error."""
        resp = api.util_rnpath()
        assert resp.get("status") == "error", (
            f"Expected error for missing hash, got: {resp}"
        )

    def test_rnpath_unknown_hash(self, api):
        """POST rnpath with unknown hash returns ok (tool runs, no path found)."""
        resp = api.util_rnpath(hash=UNKNOWN_HASH)
        assert resp.get("status") == "ok"
        data = resp.get("data", {})
        output = data.get("output") or data.get("raw") or ""
        # rnpath returns a message even when no path is known
        assert isinstance(output, str)

    def test_rnprobe_missing_hash_returns_error(self, api):
        """POST rnprobe with no hash returns status=error."""
        resp = api.util_rnprobe()
        assert resp.get("status") == "error", (
            f"Expected error for missing hash, got: {resp}"
        )

    def test_rnprobe_unknown_hash_times_out_gracefully(self, api):
        """POST rnprobe with unknown hash times out without crashing."""
        resp = api.util_rnprobe(hash=UNKNOWN_HASH, timeout=5)
        assert resp.get("status") == "ok"
        data = resp.get("data", {})
        # Output may indicate timeout/unreachable — not a server error
        assert data is not None

    def test_rnodeconfig_no_device_lists_devices(self, api):
        """POST rnodeconfig with no device path returns ok (list mode)."""
        resp = api.util_rnodeconfig()
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"

    def test_rncp_returns_help_text(self, api):
        """POST rncp returns ok with usage/help output."""
        resp = api.util_rncp()
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"
        data = resp.get("data", {})
        output = data.get("output") or data.get("raw") or ""
        assert output, "rncp returned empty output"

    def test_rnx_returns_help_text(self, api):
        """POST rnx returns ok with usage/help output."""
        resp = api.util_rnx()
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"
        data = resp.get("data", {})
        output = data.get("output") or data.get("raw") or ""
        assert output, "rnx returned empty output"
