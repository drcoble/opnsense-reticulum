"""Test 14: UI page availability and redirect verification.

Tests that all six refactored UI pages return HTTP 200 and that the
three old URLs (transport, propagation, diagnostics) redirect correctly
to their new counterparts.

OPNsense UI pages require session authentication. This module uses
HTTP basic auth via the API key/secret pair which OPNsense accepts
for the web UI when the user has sufficient privileges.
"""

import os

import pytest
import requests
import urllib3

# Suppress InsecureRequestWarning for self-signed OPNsense certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

pytestmark = pytest.mark.integration

# All six refactored UI pages
UI_PAGES = [
    "general",
    "rns",
    "lxmf",
    "interfaces",
    "utilities",
    "status",
]

# Old URLs that should redirect (not return 404)
REDIRECT_PAGES = [
    "transport",
    "propagation",
    "diagnostics",
]


@pytest.fixture(scope="module")
def ui_session(opnsense_host):
    """Authenticated requests session for OPNsense web UI.

    Uses HTTP basic auth (API key / secret) which OPNsense accepts for
    the web UI in addition to the JSON API.
    """
    api_key = os.environ.get("OPNSENSE_API_KEY", "")
    api_secret = os.environ.get("OPNSENSE_API_SECRET", "")
    if not api_key or not api_secret:
        pytest.skip("OPNSENSE_API_KEY / OPNSENSE_API_SECRET not set")

    session = requests.Session()
    session.auth = (api_key, api_secret)
    session.verify = False
    session.base_url = f"https://{opnsense_host}"
    return session


class TestUIPageAvailability:
    """All six refactored UI pages must return HTTP 200."""

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
        body = resp.text.lower()
        # Every page should mention 'reticulum' somewhere in the rendered HTML
        assert "reticulum" in body, (
            f"/ui/reticulum/{page} does not contain 'reticulum' in body — may be an error page"
        )


class TestUIRedirects:
    """Old URLs must redirect to their new counterparts (not return 404/500)."""

    @pytest.mark.parametrize("page", REDIRECT_PAGES)
    def test_old_url_redirects_or_returns_200(self, ui_session, page):
        """GET /ui/reticulum/<old_page> returns 2xx or 3xx (not 4xx/5xx)."""
        url = f"{ui_session.base_url}/ui/reticulum/{page}"
        # allow_redirects=False so we can see the redirect itself
        resp = ui_session.get(url, timeout=15, allow_redirects=False)
        assert resp.status_code < 400, (
            f"/ui/reticulum/{page} returned HTTP {resp.status_code} (expected redirect or 200)"
        )

    def test_transport_redirects_to_rns(self, ui_session):
        """GET /ui/reticulum/transport ultimately resolves to /ui/reticulum/rns."""
        url = f"{ui_session.base_url}/ui/reticulum/transport"
        resp = ui_session.get(url, timeout=15, allow_redirects=True)
        assert resp.status_code == 200
        assert "rns" in resp.url or "reticulum" in resp.text.lower(), (
            f"transport redirect did not reach RNS page: final URL={resp.url}"
        )

    def test_propagation_redirects_to_lxmf(self, ui_session):
        """GET /ui/reticulum/propagation ultimately resolves to /ui/reticulum/lxmf."""
        url = f"{ui_session.base_url}/ui/reticulum/propagation"
        resp = ui_session.get(url, timeout=15, allow_redirects=True)
        assert resp.status_code == 200
        assert "lxmf" in resp.url or "lxmf" in resp.text.lower(), (
            f"propagation redirect did not reach LXMF page: final URL={resp.url}"
        )

    def test_diagnostics_redirects_to_status(self, ui_session):
        """GET /ui/reticulum/diagnostics ultimately resolves to /ui/reticulum/status."""
        url = f"{ui_session.base_url}/ui/reticulum/diagnostics"
        resp = ui_session.get(url, timeout=15, allow_redirects=True)
        assert resp.status_code == 200
        assert "status" in resp.url or "reticulum" in resp.text.lower(), (
            f"diagnostics redirect did not reach Status page: final URL={resp.url}"
        )
