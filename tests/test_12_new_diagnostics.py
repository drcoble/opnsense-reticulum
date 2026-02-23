"""Test 12: Extended diagnostics API endpoints.

Tests the diagnostics endpoints: generalStatus, rnsdInfo, interfacesDetail.
Requires rnsd to be running with at least one interface configured.
"""

import time

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True, scope="module")
def ensure_rnsd_running(request):
    """Start rnsd with an AutoInterface before new diagnostics tests."""
    api = request.getfixturevalue("api")

    api.set_settings({"enabled": "1"})
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
    api.set_settings({"enabled": "0"})


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
        if isinstance(uptime, (int, float)):
            assert uptime >= 0


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
