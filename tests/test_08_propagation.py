"""Test 08: LXMF removal verification.

Verifies that all LXMF/propagation functionality has been cleanly removed
from the plugin. These tests confirm that removed API endpoints return 404
and that lxmd is not present on the system.
"""

import pytest
import requests

pytestmark = pytest.mark.integration


class TestLXMFEndpointsRemoved:
    """Removed LXMF/propagation API endpoints must return 404."""

    def _raw_get(self, api, path):
        """Issue a raw GET against the OPNsense API, returning the Response object."""
        url = f"{api.base_url}/{path}"
        resp = api.session.get(url, timeout=15)
        return resp

    def _raw_post(self, api, path, json=None):
        """Issue a raw POST against the OPNsense API, returning the Response object."""
        url = f"{api.base_url}/{path}"
        resp = api.session.post(url, json=json or {}, timeout=15)
        return resp

    def test_get_propagation_settings_removed(self, api):
        """GET /settings/getPropagation returns 404 (endpoint removed)."""
        resp = self._raw_get(api, "reticulum/settings/getPropagation")
        assert resp.status_code == 404, (
            f"Expected 404 for removed getPropagation endpoint, got {resp.status_code}"
        )

    def test_set_propagation_settings_removed(self, api):
        """POST /settings/setPropagation returns 404 (endpoint removed)."""
        resp = self._raw_post(api, "reticulum/settings/setPropagation",
                              json={"propagation": {"enabled": "0"}})
        assert resp.status_code == 404, (
            f"Expected 404 for removed setPropagation endpoint, got {resp.status_code}"
        )

    def test_diag_propagation_removed(self, api):
        """GET /diagnostics/propagation returns 404 (endpoint removed)."""
        resp = self._raw_get(api, "reticulum/diagnostics/propagation")
        assert resp.status_code == 404, (
            f"Expected 404 for removed propagation diagnostics endpoint, got {resp.status_code}"
        )

    def test_diag_lxmf_info_removed(self, api):
        """GET /diagnostics/lxmfInfo returns 404 (endpoint removed)."""
        resp = self._raw_get(api, "reticulum/diagnostics/lxmfInfo")
        assert resp.status_code == 404, (
            f"Expected 404 for removed lxmfInfo endpoint, got {resp.status_code}"
        )

    def test_diag_propagation_detail_removed(self, api):
        """GET /diagnostics/propagationDetail returns 404 (endpoint removed)."""
        resp = self._raw_get(api, "reticulum/diagnostics/propagationDetail")
        assert resp.status_code == 404, (
            f"Expected 404 for removed propagationDetail endpoint, got {resp.status_code}"
        )


class TestLXMFNotInstalled:
    """lxmd binary and configuration must not be present."""

    def test_lxmd_binary_not_present(self, ssh):
        """lxmd binary is not installed on the system."""
        _, _, rc = ssh("which lxmd 2>/dev/null || test -f /usr/local/bin/lxmd")
        assert rc != 0, "lxmd binary found — LXMF was not cleanly removed"

    def test_lxmd_not_running(self, ssh):
        """No lxmd process is running."""
        _, _, rc = ssh("pgrep -x lxmd")
        assert rc != 0, "lxmd process found running — LXMF was not cleanly removed"

    def test_lxmd_config_dir_absent(self, ssh):
        """lxmd config directory /usr/local/etc/lxmd does not exist."""
        stdout, _, _ = ssh("test -d /usr/local/etc/lxmd && echo present || echo absent")
        assert "absent" in stdout, (
            "lxmd config directory /usr/local/etc/lxmd still exists after removal"
        )

    def test_lxmd_db_dir_absent(self, ssh):
        """lxmd database directory /var/db/lxmd does not exist."""
        stdout, _, _ = ssh("test -d /var/db/lxmd && echo present || echo absent")
        assert "absent" in stdout, (
            "lxmd database directory /var/db/lxmd still exists after removal"
        )


class TestLXMFUIPageRemoved:
    """LXMF and propagation UI pages must return 404."""

    def test_lxmf_ui_page_removed(self, ui_session):
        """GET /ui/reticulum/lxmf returns 404 (page removed)."""
        url = f"{ui_session.base_url}/ui/reticulum/lxmf"
        resp = ui_session.get(url, timeout=15, allow_redirects=False)
        assert resp.status_code == 404, (
            f"Expected 404 for removed /ui/reticulum/lxmf, got {resp.status_code}"
        )

    def test_propagation_ui_page_removed(self, ui_session):
        """GET /ui/reticulum/propagation returns 404 (page removed)."""
        url = f"{ui_session.base_url}/ui/reticulum/propagation"
        resp = ui_session.get(url, timeout=15, allow_redirects=False)
        assert resp.status_code == 404, (
            f"Expected 404 for removed /ui/reticulum/propagation, got {resp.status_code}"
        )
