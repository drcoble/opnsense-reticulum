"""
Playwright browser test fixtures for os-reticulum.

Provides authenticated browser contexts, API client helpers, and
service lifecycle fixtures for end-to-end testing against a live
OPNsense VM.

Required environment variables
-------------------------------
OPNSENSE_HOST        — hostname or IP of the OPNsense VM (no scheme)
OPNSENSE_API_KEY     — API key for REST calls
OPNSENSE_API_SECRET  — API secret for REST calls
OPNSENSE_UI_USER     — GUI login username
OPNSENSE_UI_PASS     — GUI login password
"""
import json
import os
import time

import pytest

pytest.importorskip("playwright", reason="playwright not installed — skipping browser tests")

import requests
import urllib3

from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAGE_LOAD_TIMEOUT = 30_000      # ms — maximum wait for full page navigation
ELEMENT_TIMEOUT = 10_000        # ms — maximum wait for a single element
SERVICE_START_TIMEOUT = 30_000  # ms — maximum wait for service start/stop
AJAX_SPINNER_TIMEOUT = 15_000   # ms — maximum wait for AJAX spinner to clear

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------

class OPNsenseApiClient:
    """Thin wrapper around requests.Session for the Reticulum plugin API."""

    def __init__(self, host: str, api_key: str, api_secret: str):
        self.base_url = f"https://{host}"
        self.session = requests.Session()
        self.session.auth = (api_key, api_secret)
        self.session.verify = False

    # -- Interfaces --

    def add_interface(self, data: dict) -> requests.Response:
        """POST a new interface record.

        Also tracks the returned UUID in ``_pw_created_uuids`` so that
        ``clean_interfaces`` can delete by the correct (UUID4) format.
        """
        resp = self.session.post(
            f"{self.base_url}/api/reticulum/rnsd/addInterface",
            json={"interface": data},
        )
        if resp.ok:
            uuid = resp.json().get("uuid", "")
            if uuid:
                if not hasattr(self, '_pw_created_uuids'):
                    self._pw_created_uuids = []
                self._pw_created_uuids.append(uuid)
        return resp

    def delete_interface(self, uuid: str) -> requests.Response:
        """DELETE an interface record by UUID.

        ``allow_redirects=False`` prevents requests from silently following
        a 302 redirect (which OPNsense returns when CSRF or auth checks
        fail on POSTs without a JSON Content-Type).
        """
        return self.session.post(
            f"{self.base_url}/api/reticulum/rnsd/delInterface/{uuid}",
            json={},
            allow_redirects=False,
        )

    def list_interfaces(self) -> requests.Response:
        """GET all interface records."""
        return self.session.get(
            f"{self.base_url}/api/reticulum/rnsd/searchInterfaces",
        )

    # -- General settings --

    def get_general(self) -> requests.Response:
        """GET current general settings."""
        return self.session.get(
            f"{self.base_url}/api/reticulum/rnsd/get",
        )

    def set_general(self, data: dict) -> requests.Response:
        """POST updated general settings."""
        return self.session.post(
            f"{self.base_url}/api/reticulum/rnsd/set",
            json=data,
        )

    # -- rnsd service lifecycle --

    def start_rnsd(self) -> requests.Response:
        """POST start the rnsd service."""
        return self.session.post(
            f"{self.base_url}/api/reticulum/service/start",
        )

    def stop_rnsd(self) -> requests.Response:
        """POST stop the rnsd service."""
        return self.session.post(
            f"{self.base_url}/api/reticulum/service/stop",
        )

    def rnsd_status(self) -> requests.Response:
        """GET rnsd service status."""
        return self.session.get(
            f"{self.base_url}/api/reticulum/service/rnsdStatus",
        )

    # -- lxmd service lifecycle --

    def start_lxmd(self) -> requests.Response:
        """POST start the lxmd service."""
        return self.session.post(
            f"{self.base_url}/api/reticulum/service/lxmdStart",
        )

    def stop_lxmd(self) -> requests.Response:
        """POST stop the lxmd service."""
        return self.session.post(
            f"{self.base_url}/api/reticulum/service/lxmdStop",
        )


# ---------------------------------------------------------------------------
# Fixtures — session-scoped foundation
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def base_url() -> str:
    """Session-scoped base URL derived from OPNSENSE_HOST env var.

    Returns ``https://<host>`` for use in page navigation.
    """
    host = os.environ.get("OPNSENSE_HOST")
    if not host:
        pytest.skip("OPNSENSE_HOST not set — skipping browser tests")
    return f"https://{host}"


@pytest.fixture(scope="session")
def opnsense_api_client() -> OPNsenseApiClient:
    """Session-scoped API client configured from environment variables.

    Skips the entire session if credentials are missing.
    """
    host = os.environ.get("OPNSENSE_HOST")
    key = os.environ.get("OPNSENSE_API_KEY")
    secret = os.environ.get("OPNSENSE_API_SECRET")
    if not all([host, key, secret]):
        pytest.skip(
            "OPNSENSE_HOST / OPNSENSE_API_KEY / OPNSENSE_API_SECRET not set"
        )
    return OPNsenseApiClient(host, key, secret)


@pytest.fixture(scope="session")
def login_once(base_url, browser):
    """Perform a one-time GUI login and persist storageState for reuse.

    Scope: session — runs once per test session.

    Navigates to the OPNsense login page, fills credentials from env vars,
    submits the form, waits for the dashboard, then saves browser storage
    state to ``tests/browser/fixtures/auth_state.json``.  All subsequent
    browser contexts can reuse this state to skip re-authentication.

    Yields the Path to the saved auth_state.json file.
    """
    ui_user = os.environ.get("OPNSENSE_UI_USER")
    ui_pass = os.environ.get("OPNSENSE_UI_PASS")
    if not all([ui_user, ui_pass]):
        pytest.skip("OPNSENSE_UI_USER / OPNSENSE_UI_PASS not set")

    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    # Navigate to login page — use load instead of networkidle because
    # OPNsense pages can have long-polling that blocks networkidle.
    page.goto(base_url, wait_until="load", timeout=PAGE_LOAD_TIMEOUT)

    # Wait for the login form to be ready before interacting
    page.wait_for_selector(
        'input[name="usernamefld"]', state="visible", timeout=PAGE_LOAD_TIMEOUT
    )

    page.fill('input[name="usernamefld"]', ui_user)
    page.fill('input[name="passwordfld"]', ui_pass)

    # OPNsense uses <input type="submit"> — click it and wait for navigation
    page.locator('input[type="submit"], button[type="submit"]').first.click()

    # Wait for a post-login element — the main menu proves we're logged in
    page.wait_for_selector(
        "#mainmenu",
        state="visible",
        timeout=PAGE_LOAD_TIMEOUT,
    )

    # Verify we are NOT still on the login page (OPNsense returns 200 even
    # for the login page, so HTTP status alone is not a reliable check).
    assert page.locator('input[name="usernamefld"]').count() == 0, (
        "Login failed — still on the login page after submit.  "
        "Check OPNSENSE_UI_USER / OPNSENSE_UI_PASS values."
    )

    auth_state_path = FIXTURES_DIR / "auth_state.json"
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(auth_state_path))

    page.close()
    context.close()

    yield auth_state_path


@pytest.fixture(scope="session")
def authenticated_context(login_once, browser, base_url):
    """Session-scoped BrowserContext pre-loaded with auth cookies.

    Depends on ``login_once`` to ensure storage state exists, then creates
    a new context that skips the login form on every navigation.

    After creating the context, verifies the session is actually valid by
    loading a page and checking we don't land on the login form.
    """
    context = browser.new_context(
        storage_state=str(login_once),
        ignore_https_errors=True,
    )

    # Smoke-check: load any page and confirm we're authenticated
    probe = context.new_page()
    probe.goto(base_url, wait_until="load", timeout=PAGE_LOAD_TIMEOUT)
    is_login_page = probe.locator('input[name="usernamefld"]').count() > 0
    assert not is_login_page, (
        "Stored auth_state.json did not produce a valid session — "
        "the probe page landed on the login form."
    )

    # Verify Reticulum plugin pages are reachable — OPNsense returns HTTP 200
    # with a generic layout (no plugin content) when MVC routes are not
    # registered (e.g. lighttpd was not restarted after plugin install).
    # Check for #maintabs which is the definitive proof the Volt template
    # rendered.  Note: body.inner_text() is unreliable because OPNsense's
    # sidebar navigation may contain "page not found" as link text even on
    # valid pages.
    reticulum_url = f"{base_url}/ui/reticulum/general"
    probe.goto(reticulum_url, wait_until="load", timeout=PAGE_LOAD_TIMEOUT)
    has_maintabs = probe.locator("#maintabs").count() > 0
    if not has_maintabs:
        body_text = probe.locator("body").inner_text(timeout=5000)
        full_html = probe.content()
        probe.close()
        raise AssertionError(
            f"Reticulum plugin page did not render — "
            f"navigating to {reticulum_url} did not produce #maintabs. "
            f"This usually means lighttpd was not restarted after plugin "
            f"deployment, the Volt template has a compilation error, or "
            f"the template uses {{% extends %}} (which conflicts with "
            f"Phalcon's setTemplateBefore layout wrapping).\n"
            f"Page body excerpt: {body_text[:1000]}\n"
            f"Full live DOM (first 5000 chars): {full_html[:5000]}"
        )
    probe.close()

    yield context
    context.close()


# ---------------------------------------------------------------------------
# Fixtures — function-scoped per-test helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def authenticated_page(authenticated_context):
    """Function-scoped Page with authentication and sensible timeouts.

    Opens a fresh page tab for each test and closes it on teardown.  Default
    navigation timeout is PAGE_LOAD_TIMEOUT; default element timeout is
    ELEMENT_TIMEOUT.
    """
    page = authenticated_context.new_page()
    page.set_default_navigation_timeout(PAGE_LOAD_TIMEOUT)
    page.set_default_timeout(ELEMENT_TIMEOUT)
    yield page
    page.close()


@pytest.fixture(scope="function")
def api_client(opnsense_api_client) -> OPNsenseApiClient:
    """Function-scoped alias for the session-scoped API client.

    Exists for readability in test function signatures — every test receives
    a consistently-named ``api_client`` parameter.
    """
    yield opnsense_api_client


@pytest.fixture(scope="function")
def ensure_rnsd_running(opnsense_api_client):
    """Start rnsd and poll until it reports running (up to 30 s).

    Scope: function — ensures rnsd is running before the test body executes.
    """
    opnsense_api_client.start_rnsd()
    deadline = time.monotonic() + SERVICE_START_TIMEOUT / 1000
    while time.monotonic() < deadline:
        resp = opnsense_api_client.rnsd_status()
        if resp.ok:
            body = resp.json()
            status = body.get("status", "")
            if "running" in status.lower():
                return
        time.sleep(1)
    pytest.fail("rnsd did not reach 'running' state within 30 s")


@pytest.fixture(scope="function")
def ensure_rnsd_stopped(opnsense_api_client):
    """Stop rnsd and poll until it reports stopped (up to 30 s).

    Scope: function — ensures rnsd is stopped before the test body executes.
    """
    opnsense_api_client.stop_rnsd()
    deadline = time.monotonic() + SERVICE_START_TIMEOUT / 1000
    while time.monotonic() < deadline:
        resp = opnsense_api_client.rnsd_status()
        if resp.ok:
            body = resp.json()
            status = body.get("status", "")
            if "stopped" in status.lower() or "not running" in status.lower():
                return
        time.sleep(1)
    pytest.fail("rnsd did not reach 'stopped' state within 30 s")


@pytest.fixture(scope="function")
def clean_interfaces(opnsense_api_client):
    """Teardown fixture that removes any interfaces prefixed with ``PW-``.

    Scope: function — yields control to the test, then deletes matching
    interfaces on teardown so tests leave no residual state.

    Loops until no PW- interfaces remain, because the searchInterfaces
    endpoint may return paginated results (missing some rows per call).
    """
    yield
    # searchInterfaces returns internal XML-tag UUIDs (uniqid format) which
    # differ from the model's uuid attribute (UUID4 format).  Only the UUID4
    # format works with delBase/getBase.  We must search by name, then fetch
    # each interface to get its actual UUID for deletion.
    #
    # Workaround: use searchInterfaces to find names, then iterate with
    # getInterface using the uniqid UUID — if that fails, we need another
    # approach.  Since getInterface also doesn't work with uniqid UUIDs,
    # we store created UUIDs at creation time (via _pw_created_uuids).
    for uuid in list(getattr(opnsense_api_client, '_pw_created_uuids', [])):
        opnsense_api_client.delete_interface(uuid)
    if hasattr(opnsense_api_client, '_pw_created_uuids'):
        opnsense_api_client._pw_created_uuids.clear()


@pytest.fixture(scope="function")
def seed_one_interface(opnsense_api_client):
    """Ensure a PW-Seed-TCP interface exists; create if missing.

    Scope: function — checks whether PW-Seed-TCP already exists (it may
    have been deleted by a previous test like IFC_016) and recreates it
    from ``fixtures/interfaces_seed.json`` when needed.  Does NOT delete
    on teardown so the interface remains available for other tests in the
    same session.

    Note: ``searchInterfaces`` returns uniqid-format UUIDs that differ
    from the UUID4 format returned by ``addInterface``.  Only the UUID4
    format works with ``delInterface``/``getInterface``.  We check
    existence via searchInterfaces but always create fresh if not found.
    """
    # Check if it already exists (may have survived from a previous test)
    resp = opnsense_api_client.list_interfaces()
    if resp.ok:
        for row in resp.json().get("rows", []):
            if row.get("name") == "PW-Seed-TCP":
                yield  # Interface exists, no need to create
                return

    # Create from seed fixture
    seed_path = FIXTURES_DIR / "interfaces_seed.json"
    with open(seed_path) as f:
        data = json.load(f)

    resp = opnsense_api_client.add_interface(data)
    assert resp.ok, f"Failed to seed interface: {resp.status_code} {resp.text}"
    body = resp.json()
    uuid = body.get("uuid", "")
    assert uuid, f"No UUID returned from addInterface: {body}"

    yield


@pytest.fixture(scope="function")
def save_and_restore_general(opnsense_api_client):
    """Snapshot general settings before the test and restore them after.

    Scope: function — ensures tests that modify general/rnsd settings do
    not leak state into subsequent tests.

    The GET response from getNodes() returns rich metadata for OptionField
    and BooleanField types (e.g. ``{"enabled": {"1": {"value": "Yes",
    "selected": 1}, ...}}``).  We must flatten these to scalar values
    before POSTing back, because setNodes()/setValue() expects strings,
    not arrays.
    """
    resp = opnsense_api_client.get_general()
    assert resp.ok, f"Failed to snapshot general settings: {resp.status_code}"
    original = resp.json()

    yield original

    # Flatten option metadata arrays to selected scalar values before restore.
    flat = {}
    for key, value in original.get("general", {}).items():
        if isinstance(value, dict):
            # Option/Boolean metadata: find the entry with selected == 1
            selected = None
            for opt_key, opt_meta in value.items():
                if isinstance(opt_meta, dict) and opt_meta.get("selected"):
                    selected = str(opt_key)
                    break
            if selected is not None:
                flat[key] = selected
        else:
            flat[key] = value
    opnsense_api_client.set_general({"general": flat})
