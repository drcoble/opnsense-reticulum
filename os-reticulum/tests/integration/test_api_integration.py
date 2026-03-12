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


def _get_with_params(session, path, params=None):
    return session.get(f"{_BASE}/{path}", params=params, timeout=15)


def _wait_for_status(session, endpoint, expected, timeout=15, interval=0.5):
    """Poll a status endpoint until it returns the expected value or times out."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = _get(session, endpoint)
        if r.status_code == 200:
            text = r.text.lower()
            if expected.lower() in text:
                return r
        time.sleep(interval)
    # Final attempt for assertion
    return _get(session, endpoint)


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
        assert data.get("result") == "saved", f"Expected saved, got: {data}"

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
        assert data.get("result") == "saved", f"Expected saved, got: {data}"

    def test_a302e_toggle_interface(self, api, test_interface_uuid):
        """A-302e: toggleInterface returns ok/changed."""
        if not test_interface_uuid:
            pytest.skip("No UUID — addInterface failed")
        r = _post(api, f"rnsd/toggleInterface/{test_interface_uuid}")
        assert r.status_code == 200

    def test_a302f_delete_returns_success(self, api):
        """A-302f: delInterface returns a success indicator and interface is gone."""
        # Create a temporary interface just for delete testing
        r = _post(api, "rnsd/addInterface", {
            "interface": {
                "name": "CI Delete Test",
                "type": "TCPServerInterface",
                "listen_port": "4243",
            }
        })
        uuid = r.json().get("uuid", "")
        assert uuid, "addInterface failed to return UUID for delete test"
        # Delete it
        r = _post(api, f"rnsd/delInterface/{uuid}")
        assert r.status_code == 200
        # Verify it's gone from search
        r = _get(api, "rnsd/searchInterfaces")
        assert "CI Delete Test" not in r.text


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
        assert data.get("result") == "saved", f"Expected saved, got: {data}"

    def test_a303c_get_reflects_display_name(self, api):
        """A-303c: GET lxmd/get reflects the saved display_name."""
        _post(api, "lxmd/set", {"lxmf": {"display_name": "CI Test Node"}})
        r = _get(api, "lxmd/get")
        assert r.status_code == 200
        assert r.json().get("lxmf", {}).get("display_name") == "CI Test Node"
        # Reset display_name to default to avoid state bleed into later tests
        _post(api, "lxmd/set", {"lxmf": {"display_name": "Anonymous Peer"}})


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

@pytest.mark.timeout(45)
class TestA305ServiceLifecycle:
    """A-305: rnsd service start, stop, and restart via API."""

    def test_a305a_start_returns_ok(self, api):
        """A-305a: rnsdStart returns a 200 response."""
        r = _post(api, "service/rnsdStart")
        assert r.status_code == 200

    def test_a305b_status_running_after_start(self, api):
        """A-305b: rnsdStatus reports running after start."""
        r = _wait_for_status(api, "service/rnsdStatus", "running")
        assert r.status_code == 200
        assert "running" in r.text.lower()

    def test_a305c_stop_returns_ok(self, api):
        """A-305c: rnsdStop returns a 200 response."""
        r = _post(api, "service/rnsdStop")
        assert r.status_code == 200

    def test_a305d_status_stopped_after_stop(self, api):
        """A-305d: rnsdStatus reports stopped after stop."""
        r = _wait_for_status(api, "service/rnsdStatus", "stopped")
        assert r.status_code == 200
        text = r.text.lower()
        assert "stopped" in text or "not running" in text

    def test_a305e_restart_returns_ok(self, api):
        """A-305e: rnsdRestart returns a 200 response."""
        _post(api, "service/rnsdStart")
        _wait_for_status(api, "service/rnsdStatus", "running")
        r = _post(api, "service/rnsdRestart")
        assert r.status_code == 200

    def test_a305f_status_running_after_restart(self, api):
        """A-305f: rnsdStatus reports running after restart."""
        r = _wait_for_status(api, "service/rnsdStatus", "running")
        assert r.status_code == 200
        assert "running" in r.text.lower()
        # Clean up: stop after lifecycle test
        _post(api, "service/rnsdStop")


# ---------------------------------------------------------------------------
# A-306: lxmd start blocked without rnsd
# ---------------------------------------------------------------------------

@pytest.mark.timeout(45)
class TestA306LxmdDependency:
    """A-306: lxmdStart must fail when rnsd is not running."""

    def test_a306_lxmd_blocked_without_rnsd(self, api):
        """A-306: lxmdStart returns an error when rnsd is stopped."""
        _post(api, "service/rnsdStop")
        _wait_for_status(api, "service/rnsdStatus", "stopped")
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
        data = r.json()
        assert data.get("result") not in (None, "", "error"), \
            f"Expected successful reconfigure, got: {data}"


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
        """A-309b: No-credential request must not return real API data.

        OPNsense behaviour: when no Authorization header is provided,
        OPNsense serves its HTML login page with HTTP 200 (session-based
        redirect) rather than a 401/403.  It only returns 401/403 when
        *wrong* credentials are explicitly supplied (see test_a309a).

        We accept any of: 401, 403 (traditional rejection), or 200 with a
        non-JSON / non-API body (HTML login page = access control enforced).
        A 200 that contains actual API data (e.g. a 'general' key) is a
        security failure.
        """
        r = requests.get(
            f"https://{OPNSENSE_HOST}/api/reticulum/rnsd/get",
            verify=False,
            timeout=10,
        )
        if r.status_code in (401, 403):
            pass  # traditional HTTP auth rejection
        elif r.status_code == 200:
            # OPNsense serves HTML login page (not API data) for no-credential requests
            try:
                data = r.json()
                # If we got valid JSON with "general" key, it's a real auth bypass
                assert "general" not in data, \
                    f"SECURITY: No-credential request returned API data: {r.text[:200]}"
            except (ValueError, requests.exceptions.JSONDecodeError):
                pass  # HTML response = login page = access control enforced
        else:
            pytest.fail(f"Unexpected status {r.status_code}")

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


# ---------------------------------------------------------------------------
# A-310: Standard OPNsense service endpoints (status/start/stop/restart)
# ---------------------------------------------------------------------------

@pytest.mark.timeout(45)
class TestA310StandardServiceEndpoints:
    """A-310: Standard OPNsense service endpoints (status/start/stop/restart).

    These are the endpoints that updateServiceControlUI() calls from the
    general settings page service bar.
    """

    def test_a310a_status_returns_valid_shape(self, api):
        """A-310a: GET service/status returns JSON with a 'status' key."""
        r = _get(api, "service/status")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] in ("running", "stopped")

    def test_a310b_start_and_status_running(self, api):
        """A-310b: POST service/start → GET service/status reports running."""
        r = _post(api, "service/start")
        assert r.status_code == 200
        assert "result" in r.json()
        r = _wait_for_status(api, "service/status", "running")
        assert "running" in r.text.lower()

    def test_a310c_stop_and_status_stopped(self, api):
        """A-310c: POST service/stop → GET service/status reports stopped."""
        r = _post(api, "service/stop")
        assert r.status_code == 200
        assert "result" in r.json()
        r = _wait_for_status(api, "service/status", "stopped")
        text = r.text.lower()
        assert "stopped" in text or "not running" in text

    def test_a310d_restart_and_status_running(self, api):
        """A-310d: POST service/restart → service remains running."""
        _post(api, "service/start")
        _wait_for_status(api, "service/status", "running")
        r = _post(api, "service/restart")
        assert r.status_code == 200
        assert "result" in r.json()
        r = _wait_for_status(api, "service/status", "running")
        assert "running" in r.text.lower()
        # Clean up
        _post(api, "service/stop")
        _wait_for_status(api, "service/status", "stopped")

    def test_a310e_status_field_is_exactly_status(self, api):
        """A-310e: Verify JSON key is exactly 'status', not 'state' or variant."""
        r = _get(api, "service/status")
        data = r.json()
        assert "status" in data, f"Expected 'status' key, got keys: {list(data.keys())}"
        assert "state" not in data, "Response should use 'status' not 'state'"


# ---------------------------------------------------------------------------
# A-311: UpdateOnlyTextField masking + cross-field validation
# ---------------------------------------------------------------------------

class TestA311SecurityAndValidation:
    """A-311: UpdateOnlyTextField masking + cross-field validation rules.

    Verifies that sensitive fields are not exposed in GET responses and
    that cross-field validation rules are enforced on the live API.
    """

    # --- UpdateOnlyTextField masking ---

    def test_a311a_rpc_key_not_exposed_in_get(self, api):
        """A-311a: rpc_key is not returned in GET rnsd/get response.

        rpc_key is UpdateOnlyTextField — it should be absent or empty
        in GET responses even after being set.
        """
        # Set a valid rpc_key value
        test_key = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        _post(api, "rnsd/set", {"general": {"rpc_key": test_key}})
        # GET and verify it's masked
        r = _get(api, "rnsd/get")
        assert r.status_code == 200
        general = r.json().get("general", {})
        rpc_key_value = general.get("rpc_key", "")
        assert rpc_key_value != test_key, \
            f"SECURITY: rpc_key was returned in GET response: {rpc_key_value}"
        assert rpc_key_value == "" or rpc_key_value is None, \
            f"SECURITY: rpc_key should be empty/absent, got: {rpc_key_value}"
        # Clean up: clear rpc_key
        _post(api, "rnsd/set", {"general": {"rpc_key": ""}})

    def test_a311b_passphrase_not_exposed_in_get_interface(self, api):
        """A-311b: interface passphrase is not returned in getInterface.

        passphrase is UpdateOnlyTextField — should be masked in GET.
        """
        # Create interface with a passphrase
        r = _post(api, "rnsd/addInterface", {
            "interface": {
                "name": "CI Passphrase Test",
                "type": "TCPServerInterface",
                "listen_port": "4250",
                "passphrase": "mysecretpassphrase",
            }
        })
        uuid = r.json().get("uuid", "")
        try:
            assert uuid, "addInterface failed"
            # GET and verify passphrase is masked
            r = _get(api, f"rnsd/getInterface/{uuid}")
            assert r.status_code == 200
            iface = r.json().get("interface", {})
            passphrase_value = iface.get("passphrase", "")
            assert passphrase_value != "mysecretpassphrase", \
                f"SECURITY: passphrase returned in GET: {passphrase_value}"
            assert passphrase_value == "" or passphrase_value is None, \
                f"SECURITY: passphrase should be empty, got: {passphrase_value}"
        finally:
            if uuid:
                _post(api, f"rnsd/delInterface/{uuid}")

    # --- GET response completeness ---

    def test_a311c_get_general_enumerates_all_fields(self, api):
        """A-311c: GET rnsd/get returns all expected general fields."""
        r = _get(api, "rnsd/get")
        assert r.status_code == 200
        general = r.json().get("general", {})
        expected_fields = {
            "enabled", "enable_transport", "share_instance",
            "shared_instance_port", "instance_control_port",
            "panic_on_interface_error", "respond_to_probes",
            "enable_remote_management", "remote_management_allowed",
            "loglevel", "logfile",
        }
        missing = expected_fields - set(general.keys())
        assert not missing, f"Missing fields in GET rnsd/get: {missing}"

    # --- Cross-field validation: port conflict ---

    def test_a311d_port_conflict_rejected(self, api):
        """A-311d: Setting shared_instance_port == instance_control_port is rejected."""
        r = _post(api, "rnsd/set", {
            "general": {
                "shared_instance_port": "37428",
                "instance_control_port": "37428",
            }
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("result") != "saved", \
            "Port conflict should have been rejected"
        assert "validations" in data, \
            f"Expected validation error for port conflict, got: {data}"
        # Reset to defaults
        _post(api, "rnsd/set", {
            "general": {
                "shared_instance_port": "37428",
                "instance_control_port": "37429",
            }
        })

    # --- Cross-field validation: stamp floor ---

    def test_a311e_stamp_floor_exact_boundary_passes(self, api):
        """A-311e: stamp_cost_target=16, flexibility=3 (16-3=13) passes."""
        r = _post(api, "lxmd/set", {
            "lxmf": {
                "stamp_cost_target": "16",
                "stamp_cost_flexibility": "3",
            }
        })
        assert r.status_code == 200
        assert r.json().get("result") == "saved", \
            f"Stamp floor at exact boundary should pass: {r.json()}"

    def test_a311f_stamp_floor_one_below_fails(self, api):
        """A-311f: stamp_cost_target=16, flexibility=4 (16-4=12 < 13) fails."""
        r = _post(api, "lxmd/set", {
            "lxmf": {
                "stamp_cost_target": "16",
                "stamp_cost_flexibility": "4",
            }
        })
        assert r.status_code == 200
        data = r.json()
        assert data.get("result") != "saved", \
            "Stamp floor violation should have been rejected"
        assert "validations" in data, \
            f"Expected validation error for stamp floor, got: {data}"
        # Reset to valid values
        _post(api, "lxmd/set", {
            "lxmf": {
                "stamp_cost_target": "16",
                "stamp_cost_flexibility": "3",
            }
        })

    # --- Cross-field validation: interface name uniqueness ---

    def test_a311g_duplicate_interface_name_rejected(self, api):
        """A-311g: Adding two interfaces with the same name is rejected."""
        uuid1 = ""
        uuid2 = ""
        try:
            r = _post(api, "rnsd/addInterface", {
                "interface": {
                    "name": "CI Duplicate Test",
                    "type": "TCPServerInterface",
                    "listen_port": "4260",
                }
            })
            uuid1 = r.json().get("uuid", "")
            assert uuid1, "First addInterface failed"

            # Try adding a second with the same name
            r = _post(api, "rnsd/addInterface", {
                "interface": {
                    "name": "CI Duplicate Test",
                    "type": "TCPServerInterface",
                    "listen_port": "4261",
                }
            })
            uuid2 = r.json().get("uuid", "")
            # The second add may return a UUID but validation should fail on save,
            # or it may not return a UUID at all
            data = r.json()
            has_validation_error = "validations" in data or data.get("result") == "failed"
            assert has_validation_error, \
                f"Duplicate interface name should be rejected, got: {data}"
        finally:
            if uuid1:
                _post(api, f"rnsd/delInterface/{uuid1}")
            if uuid2:
                _post(api, f"rnsd/delInterface/{uuid2}")

    # --- Validation error response structure ---

    def test_a311h_validation_error_has_correct_shape(self, api):
        """A-311h: Validation errors return {result: 'failed', validations: {...}}."""
        r = _post(api, "rnsd/set", {"general": {"loglevel": "99"}})
        assert r.status_code == 200
        data = r.json()
        assert data.get("result") == "failed", \
            f"Expected result='failed', got: {data}"
        assert "validations" in data, \
            f"Expected 'validations' key, got: {data}"
        assert isinstance(data["validations"], dict), \
            f"Expected validations to be a dict, got: {type(data['validations'])}"


# ---------------------------------------------------------------------------
# A-312: lxmd service lifecycle and extended dependency tests
# ---------------------------------------------------------------------------

@pytest.mark.timeout(60)
class TestA312LxmdLifecycle:
    """A-312: Full lxmd service lifecycle and extended dependency tests.

    Tests the complete lxmd start/status/stop/restart cycle and verifies
    the rnsd dependency is enforced on both start and restart.

    Prerequisites: rnsd and lxmd must both be stopped before this suite runs.
    Each test that changes state is ordered to be idempotent as a sequence;
    individual tests that require a prior state call _wait_for_status to guard
    against timing races rather than relying on fixed sleeps.
    """

    def test_a312a_lxmd_status_stopped_initially(self, api):
        """A-312a: lxmdStatus returns 'stopped' when lxmd is not running."""
        # Ensure both services are stopped before the lifecycle sequence begins
        _post(api, "service/lxmdStop")
        _post(api, "service/rnsdStop")
        _wait_for_status(api, "service/rnsdStatus", "stopped")
        r = _get(api, "service/lxmdStatus")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data, f"Expected 'status' key, got: {data}"
        assert data["status"] == "stopped"

    def test_a312b_lxmd_start_succeeds_with_rnsd(self, api):
        """A-312b: lxmdStart succeeds when rnsd is running."""
        # Start rnsd first — lxmd depends on it
        _post(api, "service/rnsdStart")
        _wait_for_status(api, "service/rnsdStatus", "running")
        # Now start lxmd
        r = _post(api, "service/lxmdStart")
        assert r.status_code == 200
        data = r.json()
        assert data.get("result") != "error", \
            f"lxmdStart should succeed when rnsd is running, got: {data}"

    def test_a312c_lxmd_status_running(self, api):
        """A-312c: lxmdStatus reports 'running' after successful start."""
        r = _wait_for_status(api, "service/lxmdStatus", "running")
        assert r.status_code == 200
        assert r.json().get("status") == "running"

    def test_a312d_lxmd_stop(self, api):
        """A-312d: lxmdStop returns a 200 with a result key."""
        r = _post(api, "service/lxmdStop")
        assert r.status_code == 200
        assert "result" in r.json()

    def test_a312e_lxmd_status_stopped_after_stop(self, api):
        """A-312e: lxmdStatus reports 'stopped' after lxmdStop."""
        r = _wait_for_status(api, "service/lxmdStatus", "stopped")
        assert r.status_code == 200
        assert r.json().get("status") == "stopped"

    def test_a312f_lxmd_restart_succeeds_with_rnsd(self, api):
        """A-312f: lxmdRestart succeeds when rnsd is running."""
        # Start lxmd first so restart has something to restart
        _post(api, "service/lxmdStart")
        _wait_for_status(api, "service/lxmdStatus", "running")
        # Restart
        r = _post(api, "service/lxmdRestart")
        assert r.status_code == 200
        data = r.json()
        assert data.get("result") != "error", \
            f"lxmdRestart should succeed when rnsd is running, got: {data}"
        # Verify lxmd comes back up after restart
        r = _wait_for_status(api, "service/lxmdStatus", "running")
        assert r.json().get("status") == "running"

    def test_a312g_lxmd_restart_blocked_without_rnsd(self, api):
        """A-312g: lxmdRestart fails when rnsd is not running.

        lxmdRestartAction() has the same rnsd dependency guard as
        lxmdStartAction().  A-306 covers the start path; this test covers
        the restart path which was previously untested.
        """
        # Stop both services so rnsd is definitely absent
        _post(api, "service/lxmdStop")
        _wait_for_status(api, "service/lxmdStatus", "stopped")
        _post(api, "service/rnsdStop")
        _wait_for_status(api, "service/rnsdStatus", "stopped")
        # Attempt restart — must be rejected by the dependency guard
        r = _post(api, "service/lxmdRestart")
        assert r.status_code == 200
        text = r.text.lower()
        assert any(k in text for k in ("error", "cannot", "failed", "rnsd")), \
            f"Expected dependency error for lxmdRestart without rnsd, got: {r.text[:200]}"

    def test_a312h_cleanup(self, api):
        """A-312h: Stop both services after lifecycle tests to leave a clean state."""
        _post(api, "service/lxmdStop")
        _post(api, "service/rnsdStop")
        _wait_for_status(api, "service/lxmdStatus", "stopped")
        _wait_for_status(api, "service/rnsdStatus", "stopped")


# ---------------------------------------------------------------------------
# A-313: Interface type CRUD coverage
# ---------------------------------------------------------------------------

class TestA313InterfaceTypes:
    """A-313: Interface type CRUD coverage.

    Verifies that each interface type can be created, retrieved, and deleted
    via the API. Only TCPServerInterface was previously tested (A-302).
    """

    def _create_and_verify(self, api, iface_data):
        """Helper: create interface, verify round-trip, delete."""
        r = _post(api, "rnsd/addInterface", {"interface": iface_data})
        assert r.status_code == 200, f"addInterface returned {r.status_code}"
        uuid = r.json().get("uuid", "")
        assert uuid, f"No UUID returned for {iface_data.get('type')}: {r.json()}"
        try:
            # Verify round-trip
            r = _get(api, f"rnsd/getInterface/{uuid}")
            assert r.status_code == 200
            data = r.json().get("interface", {})
            assert data.get("name") == iface_data["name"]
            assert data.get("type") == iface_data["type"]
            return data
        finally:
            _post(api, f"rnsd/delInterface/{uuid}")

    def test_a313a_tcp_client_interface(self, api):
        """A-313a: TCPClientInterface can be created and read back."""
        self._create_and_verify(api, {
            "name": "CI TCPClient",
            "type": "TCPClientInterface",
            "target_host": "192.0.2.1",
            "target_port": "4242",
        })

    def test_a313b_udp_interface(self, api):
        """A-313b: UDPInterface can be created and read back."""
        self._create_and_verify(api, {
            "name": "CI UDP",
            "type": "UDPInterface",
            "listen_port": "4243",
            "forward_ip": "192.0.2.2",
            "forward_port": "4244",
        })

    def test_a313c_auto_interface(self, api):
        """A-313c: AutoInterface can be created with minimal fields."""
        self._create_and_verify(api, {
            "name": "CI Auto",
            "type": "AutoInterface",
        })

    def test_a313d_rnode_interface(self, api):
        """A-313d: RNodeInterface can be created with radio fields."""
        self._create_and_verify(api, {
            "name": "CI RNode",
            "type": "RNodeInterface",
            "port": "/dev/cuaU0",
            "frequency": "868000000",
            "bandwidth": "125000",
            "spreadingfactor": "7",
            "codingrate": "5",
            "txpower": "14",
        })

    def test_a313e_serial_interface(self, api):
        """A-313e: SerialInterface can be created."""
        self._create_and_verify(api, {
            "name": "CI Serial",
            "type": "SerialInterface",
            "port": "/dev/cuaU1",
            "speed": "9600",
        })

    def test_a313f_kiss_interface(self, api):
        """A-313f: KISSInterface can be created."""
        self._create_and_verify(api, {
            "name": "CI KISS",
            "type": "KISSInterface",
            "port": "/dev/cuaU2",
            "speed": "9600",
        })

    def test_a313g_ax25kiss_interface(self, api):
        """A-313g: AX25KISSInterface can be created with callsign."""
        self._create_and_verify(api, {
            "name": "CI AX25",
            "type": "AX25KISSInterface",
            "port": "/dev/cuaU3",
            "speed": "9600",
            "callsign": "N0CALL",
            "ssid": "0",
        })

    def test_a313h_pipe_interface(self, api):
        """A-313h: PipeInterface can be created with a command."""
        self._create_and_verify(api, {
            "name": "CI Pipe",
            "type": "PipeInterface",
            "command": "/usr/local/bin/pipe-helper",
        })

    def test_a313i_i2p_interface(self, api):
        """A-313i: I2PInterface can be created."""
        self._create_and_verify(api, {
            "name": "CI I2P",
            "type": "I2PInterface",
        })

    def test_a313j_backbone_interface(self, api):
        """A-313j: BackboneInterface can be created."""
        self._create_and_verify(api, {
            "name": "CI Backbone",
            "type": "BackboneInterface",
            "listen_port": "4250",
        })

    def test_a313k_rnodemulti_interface(self, api):
        """A-313k: RNodeMultiInterface can be created with sub_interfaces_raw."""
        self._create_and_verify(api, {
            "name": "CI RNodeMulti",
            "type": "RNodeMultiInterface",
            "port": "/dev/cuaU4",
            "sub_interfaces_raw": "[[CI RNodeMulti Sub 1]]\nfrequency = 868000000\nbandwidth = 125000",
        })

    def test_a313l_invalid_type_rejected(self, api):
        """A-313l: Invalid interface type is rejected by OptionField validation."""
        r = _post(api, "rnsd/addInterface", {
            "interface": {
                "name": "CI Bad Type",
                "type": "BogusInterface",
            }
        })
        assert r.status_code == 200
        data = r.json()
        has_error = "validations" in data or data.get("result") == "failed"
        assert has_error, f"Invalid type should be rejected, got: {data}"


# ---------------------------------------------------------------------------
# A-314: Info, logs, and detailed status endpoints
# ---------------------------------------------------------------------------

@pytest.mark.timeout(60)
class TestA314InfoAndLogs:
    """A-314: Info, logs, and detailed status endpoints.

    These endpoints power the dashboard widget, runtime info rows,
    and logs tab. All were previously untested.
    """

    # --- info endpoint ---

    def test_a314a_info_returns_valid_json(self, api):
        """A-314a: GET service/info returns JSON with version fields."""
        r = _get(api, "service/info")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "rns_version" in data, f"Missing rns_version, got keys: {list(data.keys())}"

    def test_a314b_info_has_version_fields(self, api):
        """A-314b: service/info contains rns_version and lxmf_version."""
        r = _get(api, "service/info")
        data = r.json()
        assert "rns_version" in data
        assert "lxmf_version" in data
        # Versions should be strings, not null
        assert isinstance(data["rns_version"], str)
        assert isinstance(data["lxmf_version"], str)

    def test_a314c_info_has_node_identity(self, api):
        """A-314c: service/info contains node_identity field."""
        r = _get(api, "service/info")
        data = r.json()
        assert "node_identity" in data
        # identity may be empty when rnsd is stopped, but key must exist
        assert isinstance(data["node_identity"], str)

    # --- rnsdInfo endpoint ---

    def test_a314d_rnsd_info_returns_expected_keys(self, api):
        """A-314d: GET service/rnsdInfo returns version, identity, uptime."""
        r = _get(api, "service/rnsdInfo")
        assert r.status_code == 200
        data = r.json()
        assert "version" in data, f"Missing version, got keys: {list(data.keys())}"
        assert "identity" in data
        assert "uptime" in data

    # --- lxmdInfo endpoint ---

    def test_a314e_lxmd_info_returns_expected_keys(self, api):
        """A-314e: GET service/lxmdInfo returns version and identity."""
        r = _get(api, "service/lxmdInfo")
        assert r.status_code == 200
        data = r.json()
        assert "version" in data, f"Missing version, got keys: {list(data.keys())}"
        assert "identity" in data

    # --- rnstatus endpoint (expanded from A-308) ---

    def test_a314f_rnstatus_stopped_has_error_key(self, api):
        """A-314f: rnstatus returns 'error' key when rnsd is stopped."""
        # Ensure rnsd is stopped
        _post(api, "service/rnsdStop")
        _wait_for_status(api, "service/rnsdStatus", "stopped")
        r = _get(api, "service/rnstatus")
        assert r.status_code == 200
        data = r.json()
        # When stopped, should have error key or empty interfaces dict
        assert "error" in data or "interfaces" in data, \
            f"Expected error or interfaces key, got: {list(data.keys())}"

    def test_a314g_rnstatus_running_has_interfaces(self, api):
        """A-314g: rnstatus returns interfaces list when rnsd is running."""
        _post(api, "service/rnsdStart")
        _wait_for_status(api, "service/rnsdStatus", "running")
        # Give rnstatus a moment to populate after daemon start
        time.sleep(3)
        r = _get(api, "service/rnstatus")
        assert r.status_code == 200
        data = r.json()
        # When running: no error key; interfaces list must be present
        if "error" not in data:
            assert "interfaces" in data, \
                f"Expected interfaces key, got: {list(data.keys())}"
            assert isinstance(data["interfaces"], list)
        # Clean up
        _post(api, "service/rnsdStop")
        _wait_for_status(api, "service/rnsdStatus", "stopped")

    # --- lxmdStatus standalone test ---

    def test_a314h_lxmd_status_returns_valid_shape(self, api):
        """A-314h: GET service/lxmdStatus returns JSON with 'status' key."""
        r = _get(api, "service/lxmdStatus")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data, f"Expected 'status' key, got: {data}"
        assert data["status"] in ("running", "stopped")

    # --- rnsdLogs endpoint ---

    def test_a314i_rnsd_logs_returns_logs_array(self, api):
        """A-314i: GET service/rnsdLogs returns a logs array."""
        r = _get(api, "service/rnsdLogs")
        assert r.status_code == 200
        data = r.json()
        assert "logs" in data, f"Missing 'logs' key, got: {list(data.keys())}"
        assert isinstance(data["logs"], list)

    def test_a314j_rnsd_logs_lines_param(self, api):
        """A-314j: rnsdLogs respects the lines parameter (clamped 10-500)."""
        r = _get_with_params(api, "service/rnsdLogs", {"lines": "10"})
        assert r.status_code == 200
        data = r.json()
        assert "logs" in data
        # Should have at most 10 lines (may have fewer if log is short)
        assert len(data["logs"]) <= 10

    # --- lxmdLogs endpoint ---

    def test_a314k_lxmd_logs_returns_logs_array(self, api):
        """A-314k: GET service/lxmdLogs returns a logs array."""
        r = _get(api, "service/lxmdLogs")
        assert r.status_code == 200
        data = r.json()
        assert "logs" in data, f"Missing 'logs' key, got: {list(data.keys())}"
        assert isinstance(data["logs"], list)


# ---------------------------------------------------------------------------
# A-315: LXMF field round-trip and validation coverage
# ---------------------------------------------------------------------------

class TestA315LxmfFieldCoverage:
    """A-315: LXMF field round-trip and validation coverage.

    Extends A-303/A-304 to cover propagation, peering, stamp cost,
    hash field, and boundary validation for the lxmf settings node.
    """

    # --- GET completeness ---

    def test_a315a_get_lxmf_enumerates_all_fields(self, api):
        """A-315a: GET lxmd/get returns all expected lxmf fields."""
        r = _get(api, "lxmd/get")
        assert r.status_code == 200
        lxmf = r.json().get("lxmf", {})
        expected = {
            "enabled", "display_name", "enable_node",
            "autopeer", "autopeer_maxdepth", "max_peers",
            "stamp_cost_target", "stamp_cost_flexibility",
            "peering_cost", "remote_peering_cost_max",
            "static_peers", "auth_required", "loglevel",
        }
        missing = expected - set(lxmf.keys())
        assert not missing, f"Missing fields in lxmd/get: {missing}"

    # --- Propagation node fields round-trip ---

    def test_a315b_propagation_fields_round_trip(self, api):
        """A-315b: Propagation node fields can be saved and read back."""
        test_values = {
            "enable_node": "1",
            "node_name": "CI Prop Node",
            "announce_interval": "60",
            "message_storage_limit": "100",
        }
        r = _post(api, "lxmd/set", {"lxmf": test_values})
        assert r.status_code == 200
        assert r.json().get("result") == "saved", f"Save failed: {r.json()}"
        # Verify round-trip
        r = _get(api, "lxmd/get")
        lxmf = r.json().get("lxmf", {})
        assert lxmf.get("enable_node") == "1"
        assert lxmf.get("node_name") == "CI Prop Node"
        # Reset
        _post(api, "lxmd/set", {"lxmf": {"enable_node": "0", "node_name": ""}})

    # --- Peering fields ---

    def test_a315c_peering_fields_round_trip(self, api):
        """A-315c: Peering topology fields can be saved and read back."""
        r = _post(api, "lxmd/set", {"lxmf": {
            "autopeer": "1",
            "autopeer_maxdepth": "6",
            "max_peers": "20",
            "from_static_only": "0",
        }})
        assert r.json().get("result") == "saved"

    # --- Peering boundary validation ---

    def test_a315d_autopeer_maxdepth_below_min_rejected(self, api):
        """A-315d: autopeer_maxdepth=0 (below min 1) is rejected."""
        r = _post(api, "lxmd/set", {"lxmf": {"autopeer_maxdepth": "0"}})
        data = r.json()
        assert data.get("result") != "saved", \
            f"autopeer_maxdepth=0 should be rejected: {data}"

    def test_a315e_autopeer_maxdepth_above_max_rejected(self, api):
        """A-315e: autopeer_maxdepth=129 (above max 128) is rejected."""
        r = _post(api, "lxmd/set", {"lxmf": {"autopeer_maxdepth": "129"}})
        data = r.json()
        assert data.get("result") != "saved", \
            f"autopeer_maxdepth=129 should be rejected: {data}"

    def test_a315f_max_peers_below_min_rejected(self, api):
        """A-315f: max_peers=0 (below min 1) is rejected."""
        r = _post(api, "lxmd/set", {"lxmf": {"max_peers": "0"}})
        data = r.json()
        assert data.get("result") != "saved", \
            f"max_peers=0 should be rejected: {data}"

    def test_a315g_max_peers_above_max_rejected(self, api):
        """A-315g: max_peers=1001 (above max 1000) is rejected."""
        r = _post(api, "lxmd/set", {"lxmf": {"max_peers": "1001"}})
        data = r.json()
        assert data.get("result") != "saved", \
            f"max_peers=1001 should be rejected: {data}"

    # --- Stamp/peering cost range validation ---

    def test_a315h_stamp_cost_target_below_min(self, api):
        """A-315h: stamp_cost_target=12 (below min 13) is rejected."""
        r = _post(api, "lxmd/set", {"lxmf": {"stamp_cost_target": "12"}})
        assert r.json().get("result") != "saved"

    def test_a315i_stamp_cost_target_above_max(self, api):
        """A-315i: stamp_cost_target=65 (above max 64) is rejected."""
        r = _post(api, "lxmd/set", {"lxmf": {"stamp_cost_target": "65"}})
        assert r.json().get("result") != "saved"

    def test_a315j_peering_cost_below_min(self, api):
        """A-315j: peering_cost=12 (below min 13) is rejected."""
        r = _post(api, "lxmd/set", {"lxmf": {"peering_cost": "12"}})
        assert r.json().get("result") != "saved"

    def test_a315k_lxmf_loglevel_above_max(self, api):
        """A-315k: lxmf loglevel=8 (above max 7) is rejected."""
        r = _post(api, "lxmd/set", {"lxmf": {"loglevel": "8"}})
        assert r.json().get("result") != "saved"

    # --- Hash field validation ---

    def test_a315l_valid_hash_accepted(self, api):
        """A-315l: Valid 32-char lowercase hex hash is accepted for static_peers."""
        valid_hash = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        r = _post(api, "lxmd/set", {"lxmf": {"static_peers": valid_hash}})
        assert r.json().get("result") == "saved", \
            f"Valid hash should be accepted: {r.json()}"
        # Verify round-trip
        r = _get(api, "lxmd/get")
        assert r.json().get("lxmf", {}).get("static_peers") == valid_hash
        # Clean up
        _post(api, "lxmd/set", {"lxmf": {"static_peers": ""}})

    def test_a315m_uppercase_hash_rejected(self, api):
        """A-315m: Uppercase hex hash is rejected (mask is lowercase only)."""
        r = _post(api, "lxmd/set", {
            "lxmf": {"static_peers": "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4"}
        })
        assert r.json().get("result") != "saved", \
            "Uppercase hash should be rejected"

    def test_a315n_short_hash_rejected(self, api):
        """A-315n: 31-char hash is rejected (too short)."""
        r = _post(api, "lxmd/set", {
            "lxmf": {"static_peers": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d"}  # 31 chars
        })
        assert r.json().get("result") != "saved", \
            "31-char hash should be rejected"

    def test_a315o_multiple_valid_hashes_accepted(self, api):
        """A-315o: Comma-separated valid hashes are accepted."""
        hashes = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4,b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5"
        r = _post(api, "lxmd/set", {"lxmf": {"static_peers": hashes}})
        assert r.json().get("result") == "saved", \
            f"Multiple valid hashes should be accepted: {r.json()}"
        # Clean up
        _post(api, "lxmd/set", {"lxmf": {"static_peers": ""}})

    def test_a315p_control_allowed_hash_accepted(self, api):
        """A-315p: control_allowed field also accepts valid hashes."""
        valid_hash = "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"
        r = _post(api, "lxmd/set", {"lxmf": {"control_allowed": valid_hash}})
        assert r.json().get("result") == "saved", \
            f"control_allowed hash should be accepted: {r.json()}"
        # Clean up
        _post(api, "lxmd/set", {"lxmf": {"control_allowed": ""}})
