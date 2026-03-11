"""
API Integration Tests — A-301 through A-309

Requires a live OPNsense VM with the os-reticulum plugin installed.

Environment variables:
  OPNSENSE_HOST       — OPNsense hostname or IP (no scheme, no trailing slash)
  OPNSENSE_API_KEY    — OPNsense API key (used as HTTP Basic auth username)
  OPNSENSE_API_SECRET — OPNsense API secret (used as HTTP Basic auth password)

Run with:
  pytest tests/integration/ -m integration -v
"""
import os
import time

import pytest
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OPNSENSE_HOST = os.environ.get("OPNSENSE_HOST", "")
API_KEY = os.environ.get("OPNSENSE_API_KEY", "")
API_SECRET = os.environ.get("OPNSENSE_API_SECRET", "")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not OPNSENSE_HOST or not API_KEY,
        reason="OPNSENSE_HOST/OPNSENSE_API_KEY env vars not set",
    ),
]

_BASE = f"https://{OPNSENSE_HOST}/api/reticulum"


# ---------------------------------------------------------------------------
# Session fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def api():
    """Requests session configured for OPNsense API key auth."""
    s = requests.Session()
    s.auth = (API_KEY, API_SECRET)
    s.verify = False
    return s


def _get(session, path):
    return session.get(f"{_BASE}/{path}", timeout=15)


def _post(session, path, data=None):
    return session.post(f"{_BASE}/{path}", json=data or {}, timeout=15)


# ---------------------------------------------------------------------------
# Fixture: managed test interface (created + torn down around A-302 tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_interface_uuid(api):
    """Create a CI test interface, yield its UUID, delete it on teardown."""
    r = _post(api, "rnsd/addInterface", {
        "interface": {
            "name": "CI Test TCP",
            "type": "TCPServerInterface",
            "listen_port": "4242",
        }
    })
    uuid = r.json().get("uuid", "") if r.status_code == 200 else ""
    yield uuid
    if uuid:
        _post(api, f"rnsd/delInterface/{uuid}")


# ---------------------------------------------------------------------------
# A-301: General settings get/set
# ---------------------------------------------------------------------------

class TestA301GeneralSettings:
    """A-301: GET/POST rnsd general settings."""

    def test_a301a_get_returns_general(self, api):
        """A-301a: GET rnsd/get returns a 'general' key."""
        r = _get(api, "rnsd/get")
        assert r.status_code == 200
        assert "general" in r.json()

    def test_a301b_set_saves_valid_data(self, api):
        """A-301b: POST rnsd/set with valid data returns saved/result."""
        r = _post(api, "rnsd/set", {"general": {"loglevel": "5"}})
        assert r.status_code == 200
        data = r.json()
        assert "saved" in data or "result" in data

    def test_a301c_get_reflects_saved_loglevel(self, api):
        """A-301c: GET rnsd/get reflects loglevel previously saved to 5."""
        _post(api, "rnsd/set", {"general": {"loglevel": "5"}})
        r = _get(api, "rnsd/get")
        assert r.status_code == 200
        assert r.json().get("general", {}).get("loglevel") == "5"
        # Reset to default
        _post(api, "rnsd/set", {"general": {"loglevel": "4"}})


# ---------------------------------------------------------------------------
# A-302: Interface CRUD cycle
# ---------------------------------------------------------------------------

class TestA302InterfaceCRUD:
    """A-302: Full interface create/read/update/toggle/delete cycle."""

    def test_a302a_add_interface_returns_uuid(self, test_interface_uuid):
        """A-302a: addInterface returns a non-empty UUID."""
        assert test_interface_uuid, "addInterface did not return a UUID"

    def test_a302b_search_finds_interface(self, api, test_interface_uuid):
        """A-302b: searchInterfaces lists the newly created interface."""
        if not test_interface_uuid:
            pytest.skip("No UUID — addInterface failed")
        r = _get(api, "rnsd/searchInterfaces")
        assert r.status_code == 200
        assert "CI Test TCP" in r.text

    def test_a302c_get_interface_returns_data(self, api, test_interface_uuid):
        """A-302c: getInterface returns the correct interface name."""
        if not test_interface_uuid:
            pytest.skip("No UUID — addInterface failed")
        r = _get(api, f"rnsd/getInterface/{test_interface_uuid}")
        assert r.status_code == 200
        assert "CI Test TCP" in r.text

    def test_a302d_set_interface_updates_port(self, api, test_interface_uuid):
        """A-302d: setInterface saves an updated listen_port."""
        if not test_interface_uuid:
            pytest.skip("No UUID — addInterface failed")
        r = _post(api, f"rnsd/setInterface/{test_interface_uuid}", {
            "interface": {"listen_port": "5555"}
        })
        assert r.status_code == 200
        data = r.json()
        assert "saved" in data or "result" in data

    def test_a302e_toggle_interface(self, api, test_interface_uuid):
        """A-302e: toggleInterface returns ok/changed."""
        if not test_interface_uuid:
            pytest.skip("No UUID — addInterface failed")
        r = _post(api, f"rnsd/toggleInterface/{test_interface_uuid}")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# A-303: LXMF get/set
# ---------------------------------------------------------------------------

class TestA303LxmfSettings:
    """A-303: GET/POST lxmd LXMF settings."""

    def test_a303a_get_returns_lxmf(self, api):
        """A-303a: GET lxmd/get returns an 'lxmf' key."""
        r = _get(api, "lxmd/get")
        assert r.status_code == 200
        assert "lxmf" in r.json()

    def test_a303b_set_saves_display_name(self, api):
        """A-303b: POST lxmd/set saves display_name."""
        r = _post(api, "lxmd/set", {"lxmf": {"display_name": "CI Test Node"}})
        assert r.status_code == 200
        data = r.json()
        assert "saved" in data or "result" in data

    def test_a303c_get_reflects_display_name(self, api):
        """A-303c: GET lxmd/get reflects the saved display_name."""
        _post(api, "lxmd/set", {"lxmf": {"display_name": "CI Test Node"}})
        r = _get(api, "lxmd/get")
        assert r.status_code == 200
        assert r.json().get("lxmf", {}).get("display_name") == "CI Test Node"


# ---------------------------------------------------------------------------
# A-304: Invalid data rejection
# ---------------------------------------------------------------------------

class TestA304Validation:
    """A-304: API rejects invalid inputs with validation errors."""

    def _assert_error(self, r):
        assert r.status_code == 200
        text = r.text.lower()
        assert any(k in text for k in ("validat", "error", "failed")), \
            f"Expected validation error, got: {r.text[:200]}"

    def test_a304a_rejects_loglevel_99(self, api):
        """A-304a: POST rnsd/set rejects loglevel=99 (out of 0–7 range)."""
        self._assert_error(_post(api, "rnsd/set", {"general": {"loglevel": "99"}}))

    def test_a304b_rejects_missing_interface_name(self, api):
        """A-304b: addInterface rejects a missing required name field."""
        self._assert_error(_post(api, "rnsd/addInterface", {
            "interface": {"type": "TCPServerInterface"}
        }))

    def test_a304c_rejects_port_out_of_range(self, api):
        """A-304c: POST rnsd/set rejects shared_instance_port=99999."""
        self._assert_error(_post(api, "rnsd/set", {
            "general": {"shared_instance_port": "99999"}
        }))

    def test_a304d_rejects_invalid_static_peers(self, api):
        """A-304d: POST lxmd/set rejects an invalid static_peers hash."""
        self._assert_error(_post(api, "lxmd/set", {
            "lxmf": {"static_peers": "NOTVALID"}
        }))


# ---------------------------------------------------------------------------
# A-305: rnsd start / stop / restart
# ---------------------------------------------------------------------------

class TestA305ServiceLifecycle:
    """A-305: rnsd service start, stop, and restart via API."""

    def test_a305a_start_returns_ok(self, api):
        """A-305a: rnsdStart returns a 200 response."""
        r = _post(api, "service/rnsdStart")
        assert r.status_code == 200

    def test_a305b_status_running_after_start(self, api):
        """A-305b: rnsdStatus reports running after start."""
        time.sleep(2)
        r = _get(api, "service/rnsdStatus")
        assert r.status_code == 200
        assert "running" in r.text.lower()

    def test_a305c_stop_returns_ok(self, api):
        """A-305c: rnsdStop returns a 200 response."""
        r = _post(api, "service/rnsdStop")
        assert r.status_code == 200

    def test_a305d_status_stopped_after_stop(self, api):
        """A-305d: rnsdStatus reports stopped after stop."""
        time.sleep(1)
        r = _get(api, "service/rnsdStatus")
        assert r.status_code == 200
        text = r.text.lower()
        assert "stopped" in text or "not running" in text

    def test_a305e_restart_returns_ok(self, api):
        """A-305e: rnsdRestart returns a 200 response."""
        _post(api, "service/rnsdStart")
        time.sleep(2)
        r = _post(api, "service/rnsdRestart")
        assert r.status_code == 200

    def test_a305f_status_running_after_restart(self, api):
        """A-305f: rnsdStatus reports running after restart."""
        time.sleep(2)
        r = _get(api, "service/rnsdStatus")
        assert r.status_code == 200
        assert "running" in r.text.lower()
        # Clean up: stop after lifecycle test
        _post(api, "service/rnsdStop")


# ---------------------------------------------------------------------------
# A-306: lxmd start blocked without rnsd
# ---------------------------------------------------------------------------

class TestA306LxmdDependency:
    """A-306: lxmdStart must fail when rnsd is not running."""

    def test_a306_lxmd_blocked_without_rnsd(self, api):
        """A-306: lxmdStart returns an error when rnsd is stopped."""
        _post(api, "service/rnsdStop")
        time.sleep(1)
        r = _post(api, "service/lxmdStart")
        assert r.status_code == 200
        text = r.text.lower()
        assert any(k in text for k in ("error", "cannot", "failed", "rnsd")), \
            f"Expected dependency error, got: {r.text[:200]}"


# ---------------------------------------------------------------------------
# A-307: Reconfigure
# ---------------------------------------------------------------------------

class TestA307Reconfigure:
    """A-307: service/reconfigure runs without error."""

    def test_a307_reconfigure_runs_without_error(self, api):
        """A-307: POST service/reconfigure returns ok/result."""
        r = _post(api, "service/reconfigure")
        assert r.status_code == 200
        text = r.text.lower()
        assert "ok" in text or "result" in text


# ---------------------------------------------------------------------------
# A-308: rnstatus returns valid JSON when stopped
# ---------------------------------------------------------------------------

class TestA308Rnstatus:
    """A-308: rnstatus endpoint returns valid JSON even when rnsd is stopped."""

    def test_a308_rnstatus_returns_valid_json(self, api):
        """A-308: GET service/rnstatus returns parseable JSON."""
        r = _get(api, "service/rnstatus")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# A-309: Authentication / unauthorized access
# ---------------------------------------------------------------------------

class TestA309Auth:
    """A-309: Unauthenticated and wrongly-authenticated requests are rejected."""

    def test_a309a_wrong_credentials_rejected(self):
        """A-309a: GET rnsd/get with wrong credentials returns 401 or 403."""
        r = requests.get(
            f"https://{OPNSENSE_HOST}/api/reticulum/rnsd/get",
            auth=("wronguser", "wrongpass"),
            verify=False,
            timeout=10,
        )
        assert r.status_code in (401, 403), \
            f"Expected 401/403, got {r.status_code}"

    def test_a309b_no_credentials_rejected(self):
        """A-309b: GET rnsd/get with no credentials returns 401 or 403."""
        r = requests.get(
            f"https://{OPNSENSE_HOST}/api/reticulum/rnsd/get",
            verify=False,
            timeout=10,
        )
        assert r.status_code in (401, 403), \
            f"Expected 401/403, got {r.status_code}"

    def test_a309c_post_without_csrf_documented(self):
        """A-309c: POST without CSRF token — documents OPNsense CSRF behaviour.

        OPNsense skips CSRF checks for API key (Basic) auth; CSRF only applies
        to session-cookie auth. This test passes in either case and records the
        observed HTTP status for documentation purposes.
        """
        r = requests.post(
            f"https://{OPNSENSE_HOST}/api/reticulum/service/reconfigure",
            json={},
            verify=False,
            timeout=10,
        )
        # 403 = CSRF rejected (cookie auth); 200/401 = Basic auth path (expected)
        assert r.status_code in (200, 401, 403), \
            f"Unexpected status {r.status_code}"
