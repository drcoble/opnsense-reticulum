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
        """POST a new interface record."""
        return self.session.post(
            f"{self.base_url}/api/reticulum/rnsd/addInterface",
            json={"interface": data},
        )

    def delete_interface(self, uuid: str) -> requests.Response:
        """DELETE an interface record by UUID."""
        return self.session.post(
            f"{self.base_url}/api/reticulum/rnsd/delInterface/{uuid}",
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

    page.goto(base_url, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
    page.fill('input[name="usernamefld"]', ui_user)
    page.fill('input[name="passwordfld"]', ui_pass)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_selector(
        "#mainmenu, div.page-content-head",
        timeout=PAGE_LOAD_TIMEOUT,
    )

    auth_state_path = FIXTURES_DIR / "auth_state.json"
    context.storage_state(path=str(auth_state_path))

    page.close()
    context.close()

    yield auth_state_path


@pytest.fixture(scope="session")
def authenticated_context(login_once, browser):
    """Session-scoped BrowserContext pre-loaded with auth cookies.

    Depends on ``login_once`` to ensure storage state exists, then creates
    a new context that skips the login form on every navigation.
    """
    context = browser.new_context(
        storage_state=str(login_once),
        ignore_https_errors=True,
    )
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
    """
    yield
    resp = opnsense_api_client.list_interfaces()
    if not resp.ok:
        return
    body = resp.json()
    rows = body.get("rows", [])
    for row in rows:
        name = row.get("name", "")
        if name.startswith("PW-"):
            opnsense_api_client.delete_interface(row["uuid"])


@pytest.fixture(scope="session")
def seed_one_interface(opnsense_api_client):
    """Create a single TCP server interface for tests that need existing data.

    Scope: session — creates the interface once from
    ``fixtures/interfaces_seed.json``, yields its UUID, and deletes it
    after the entire session completes.
    """
    seed_path = FIXTURES_DIR / "interfaces_seed.json"
    with open(seed_path) as f:
        data = json.load(f)

    resp = opnsense_api_client.add_interface(data)
    assert resp.ok, f"Failed to seed interface: {resp.status_code} {resp.text}"
    body = resp.json()
    uuid = body.get("uuid", "")
    assert uuid, f"No UUID returned from addInterface: {body}"

    yield uuid

    opnsense_api_client.delete_interface(uuid)


@pytest.fixture(scope="function")
def save_and_restore_general(opnsense_api_client):
    """Snapshot general settings before the test and restore them after.

    Scope: function — ensures tests that modify general/rnsd settings do
    not leak state into subsequent tests.
    """
    resp = opnsense_api_client.get_general()
    assert resp.ok, f"Failed to snapshot general settings: {resp.status_code}"
    original = resp.json()

    yield original

    opnsense_api_client.set_general(original)
