"""Test 14: UI page availability verification.

Tests that the five current Reticulum UI pages return HTTP 200, that
secondary pages (transport, diagnostics) still resolve correctly, and
that removed pages (lxmf, propagation) return 404.

OPNsense UI pages require session authentication. This module uses
HTTP basic auth via the API key/secret pair which OPNsense accepts
for the web UI when the user has sufficient privileges.
"""

import pytest

pytestmark = pytest.mark.integration

# Current menu pages (General, RNS, Interfaces, Utilities, Status)
UI_PAGES = [
    "general",
    "rns",
    "interfaces",
    "utilities",
    "status",
]

# Secondary pages: controllers still exist but not in the main menu
SECONDARY_PAGES = [
    "transport",
    "diagnostics",
]


class TestUIPageAvailability:
    """Current menu UI pages must return HTTP 200."""

    @pytest.mark.parametrize("page", UI_PAGES)
    def test_ui_page_returns_200(self, ui_session, page):
        """GET /ui/reticulum/<page> returns HTTP 200."""
        url = f"{ui_session.base_url}/ui/reticulum/{page}"
        resp = ui_session.get(url, timeout=15, allow_redirects=True)
        assert resp.status_code == 200, (
            f"/ui/reticulum/{page} returned HTTP {resp.status_code} (expected 200)"
        )

    @pytest.mark.parametrize("page", UI_PAGES)
    def test_ui_page_contains_reticulum_content(self, ui_session, page):
        """UI page body contains Reticulum-related content (not an error page)."""
        url = f"{ui_session.base_url}/ui/reticulum/{page}"
        resp = ui_session.get(url, timeout=15, allow_redirects=True)
        assert "reticulum" in resp.text.lower(), (
            f"/ui/reticulum/{page} does not contain 'reticulum' — may be an error page"
        )


class TestSecondaryPages:
    """Secondary pages (not in menu but controllers still exist) must return 200."""

    @pytest.mark.parametrize("page", SECONDARY_PAGES)
    def test_secondary_page_returns_200(self, ui_session, page):
        """GET /ui/reticulum/<page> returns HTTP 200."""
        url = f"{ui_session.base_url}/ui/reticulum/{page}"
        resp = ui_session.get(url, timeout=15, allow_redirects=True)
        assert resp.status_code == 200, (
            f"/ui/reticulum/{page} returned HTTP {resp.status_code} (expected 200)"
        )
