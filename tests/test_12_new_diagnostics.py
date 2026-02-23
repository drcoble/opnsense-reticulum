"""Test 12: New status/diagnostics API endpoints.

Tests the five diagnostics endpoints added in the UI refactor:
generalStatus, rnsdInfo, lxmfInfo, propagationDetail, interfacesDetail.

Requires rnsd to be running with at least one interface configured.
"""

import time

import pytest

pytestmark = pytest.mark.integration

LXMD_BIN = "/usr/local/bin/lxmd"


@pytest.fixture(autouse=True, scope="module")
def ensure_rnsd_running(request):
    """Start rnsd with an AutoInterface before new diagnostics tests."""
    api = request.getfixturevalue("api")

    api.set_settings({"enabled": "1", "enable_lxmf": "0"})
    result = api.add_interface({
        "name": "CI Diag New Test",
        "interfaceType": "AutoInterface",
        "enabled": "1",
        "auto_group_id": "ci-diag-new",
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
    api.set_settings({"enabled": "0", "enable_lxmf": "0"})


class TestGeneralStatus:
    """generalStatus endpoint structure and content."""

    def test_general_status_returns_ok(self, api):
        """GET generalStatus returns status=ok."""
        resp = api.diag_general_status()
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"

    def test_general_status_has_interface_counts(self, api):
        """generalStatus data contains interface count keys."""
        resp = api.diag_general_status()
        data = resp.get("data", {})
        for key in ("total_interfaces", "enabled_interfaces", "up_interfaces"):
            assert key in data, f"Missing key '{key}' in generalStatus data: {data}"

    def test_general_status_bandwidth_by_medium(self, api):
        """generalStatus data contains bandwidth_by_medium dict."""
        resp = api.diag_general_status()
        data = resp.get("data", {})
        assert "bandwidth_by_medium" in data, f"Missing bandwidth_by_medium: {data}"
        assert isinstance(data["bandwidth_by_medium"], dict)

    def test_general_status_interface_counts_are_numeric(self, api):
        """Interface count values are non-negative integers."""
        resp = api.diag_general_status()
        data = resp.get("data", {})
        for key in ("total_interfaces", "enabled_interfaces", "up_interfaces"):
            val = data.get(key, -1)
            assert isinstance(val, (int, float)) and val >= 0, (
                f"{key} is not a non-negative number: {val}"
            )


class TestRNSDInfo:
    """rnsdInfo endpoint — daemon version and uptime."""

    def test_rnsd_info_returns_ok(self, api):
        """GET rnsdInfo returns status=ok."""
        resp = api.diag_rnsd_info()
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"

    def test_rnsd_info_running_true(self, api):
        """rnsdInfo reports running=True when rnsd is active."""
        resp = api.diag_rnsd_info()
        data = resp.get("data", {})
        assert data.get("running") is True, f"Expected running=True: {data}"

    def test_rnsd_info_version_non_empty(self, api):
        """rnsdInfo returns a non-empty version string."""
        resp = api.diag_rnsd_info()
        data = resp.get("data", {})
        version = data.get("version", "")
        assert isinstance(version, str) and version, f"Empty version in rnsdInfo: {data}"

    def test_rnsd_info_uptime_non_negative(self, api):
        """rnsdInfo returns a non-negative uptime value."""
        resp = api.diag_rnsd_info()
        data = resp.get("data", {})
        uptime = data.get("uptime")
        assert uptime is not None, f"Missing uptime in rnsdInfo: {data}"
        # uptime may be a string description or a number
        if isinstance(uptime, (int, float)):
            assert uptime >= 0


class TestLXMFInfo:
    """lxmfInfo endpoint — LXMD daemon state."""

    def test_lxmf_info_stopped_when_disabled(self, api):
        """lxmfInfo reports running=False when lxmd is not running."""
        resp = api.diag_lxmf_info()
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"
        data = resp.get("data", {})
        assert data.get("running") is False, (
            f"Expected running=False (lxmd disabled), got: {data}"
        )

    def test_lxmf_info_running_when_enabled(self, api, ssh, wait_for_service):
        """lxmfInfo reports running=True when lxmd is active."""
        # Enable LXMF unbound so it can start without rnsd dependency issues
        api.set_settings({"enable_lxmf": "1", "lxmf_bind_to_rnsd": "0"})
        api.set_propagation({"enabled": "1"})
        api.service_reconfigure()
        time.sleep(3)

        ssh("configd reticulum start_lxmd", timeout=30)

        def lxmd_up():
            _, _, rc = ssh(f"pgrep -f {LXMD_BIN}")
            return rc == 0

        wait_for_service(lxmd_up, "lxmd running", timeout=30)

        resp = api.diag_lxmf_info()
        assert resp.get("status") == "ok"
        data = resp.get("data", {})
        assert data.get("running") is True, f"Expected running=True: {data}"
        assert data.get("version"), f"Empty version while lxmd running: {data}"

        # Cleanup
        ssh("configd reticulum stop_lxmd", timeout=30)
        time.sleep(2)
        api.set_propagation({"enabled": "0"})
        api.set_settings({"enable_lxmf": "0", "lxmf_bind_to_rnsd": "1"})
        api.service_reconfigure()


class TestPropagationDetail:
    """propagationDetail endpoint structure."""

    def test_propagation_detail_returns_ok(self, api):
        """GET propagationDetail returns status=ok."""
        resp = api.diag_propagation_detail()
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"

    def test_propagation_detail_has_expected_keys(self, api):
        """propagationDetail data contains all required keys."""
        resp = api.diag_propagation_detail()
        data = resp.get("data", {})
        for key in ("running", "message_count", "storage_mb", "storage_used_pct", "peer_count", "errors"):
            assert key in data, f"Missing key '{key}' in propagationDetail: {data}"

    def test_storage_mb_is_non_negative(self, api):
        """storage_mb is a non-negative number."""
        resp = api.diag_propagation_detail()
        data = resp.get("data", {})
        storage_mb = data.get("storage_mb", -1)
        assert isinstance(storage_mb, (int, float)) and storage_mb >= 0, (
            f"storage_mb is not non-negative: {storage_mb}"
        )

    def test_storage_used_pct_in_range(self, api):
        """storage_used_pct is between 0 and 100."""
        resp = api.diag_propagation_detail()
        data = resp.get("data", {})
        pct = data.get("storage_used_pct", -1)
        assert isinstance(pct, (int, float)) and 0 <= pct <= 100, (
            f"storage_used_pct out of range: {pct}"
        )


class TestInterfacesDetail:
    """interfacesDetail endpoint."""

    def test_interfaces_detail_returns_ok(self, api):
        """GET interfacesDetail returns status=ok."""
        resp = api.diag_interfaces_detail()
        assert resp.get("status") == "ok", f"Unexpected status: {resp}"

    def test_interfaces_detail_has_data(self, api):
        """interfacesDetail data is non-null."""
        resp = api.diag_interfaces_detail()
        assert resp.get("data") is not None, f"interfacesDetail returned null data: {resp}"
