# Playwright Testing Infrastructure Specification
**Date:** 2026-03-12
**Status:** draft
**Source:** Technical documentarian — spec authored from context; no code implemented yet

---

## Overview

This document specifies the complete infrastructure design for adding Playwright browser automation tests to the OPNsense Reticulum plugin. It covers directory layout, dependencies, configuration, authentication, fixtures, page objects, test data management, CI integration, and naming conventions.

No code exists yet. This spec is the authoritative reference for the implementation phase.

---

## 1. Directory Structure

Playwright tests live inside the existing `os-reticulum/tests/` tree as a new `browser/` subdirectory. This keeps all test types co-located, consistent with how `integration/`, `template/`, and `model/` are organized today.

```
os-reticulum/tests/
├── conftest.py                        # Existing shared fixtures (unchanged)
├── pytest.ini                         # Existing config (markers extended here)
├── requirements-test.txt              # Existing (unchanged)
├── requirements-browser.txt           # NEW — Playwright-specific deps
├── browser/
│   ├── __init__.py
│   ├── conftest.py                    # Browser-specific fixtures (auth, API client, page objects)
│   ├── pages/                         # Page Object Model
│   │   ├── __init__.py
│   │   ├── base_page.py               # BasePage: navigation helpers, alert handling
│   │   ├── general_page.py            # GeneralPage: General Settings form
│   │   ├── interfaces_page.py         # InterfacesPage: grid + modal CRUD
│   │   ├── lxmf_page.py               # LxmfPage: Propagation Node form
│   │   ├── logs_page.py               # LogsPage: dual-tab log viewer
│   │   └── dashboard_page.py          # DashboardPage: widget add/inspect
│   ├── fixtures/
│   │   ├── auth_state.json            # Saved browser storage state (gitignored)
│   │   └── interfaces_seed.json       # Static test interface definitions
│   ├── test_PW_general.py             # PW-101–PW-120: General Settings page
│   ├── test_PW_interfaces.py          # PW-201–PW-240: Interfaces page
│   ├── test_PW_lxmf.py                # PW-301–PW-320: Propagation Node page
│   ├── test_PW_logs.py                # PW-401–PW-410: Log Viewer
│   └── test_PW_widget.py              # PW-501–PW-510: Dashboard widget
```

**Naming rationale:**
- `browser/` rather than `playwright/` or `e2e/` — the directory names what the tests *use*, not what they *test*
- `fixtures/auth_state.json` is gitignored because it contains a live session cookie tied to a specific VM
- `fixtures/interfaces_seed.json` is committed — it is static JSON, not credentials

---

## 2. Dependencies

### Separate requirements file

Playwright and pytest-playwright must **not** be added to `requirements-test.txt`. The existing file is installed in the unit-test CI job (Ubuntu GitHub Actions, no browser), and adding Playwright there would require browser binaries on a runner that does not need them and would slow down every unit test run.

Create `os-reticulum/tests/requirements-browser.txt`:

```
playwright>=1.44
pytest-playwright>=0.5
pytest>=7.4
pytest-timeout>=2.1
requests>=2.31
```

`requests` is repeated here so the browser conftest can use it for API setup/teardown without depending on the unit-test venv. `pytest` and `pytest-timeout` are repeated for the same reason — the browser test job installs only this file.

**Browser binary installation** is handled by a separate CI step (see Section 8), not by pip. The command is:

```sh
playwright install chromium
```

Only Chromium is installed. See Section 3 for rationale.

---

## 3. Configuration

### No playwright.config.ts

The project does not use a TypeScript test runner. All Playwright tests use the **pytest-playwright** plugin, which is configured through `pytest.ini` and `browser/conftest.py`. There is no `playwright.config.ts`.

### pytest.ini additions

Add the `browser` marker to the existing `pytest.ini`:

```ini
[pytest]
testpaths = tests
markers =
    unit: Tests that run without a live OPNsense VM (template rendering, model validation, security injection)
    integration: Tests that require a live OPNsense VM (API endpoints, service lifecycle)
    browser: Tests that require a live OPNsense VM and a real browser (Playwright)
```

### Browser selection: Chromium only

OPNsense's web UI is built for modern browsers; there is no requirement to test Safari or Firefox compatibility. Chromium is the only browser installed in CI. pytest-playwright defaults to Chromium, so no `--browser` flag is needed unless adding multi-browser coverage in the future.

### Base URL

The base URL is derived from `OPNSENSE_HOST` at runtime. It is set as a pytest-playwright `base_url` fixture override in `browser/conftest.py`:

```python
@pytest.fixture(scope="session")
def base_url():
    host = os.environ["OPNSENSE_HOST"]
    return f"https://{host}"
```

This overrides pytest-playwright's built-in `base_url` fixture. All `page.goto()` calls in tests use relative paths (e.g., `page.goto("/ui/reticulum/general")`).

### Headless mode

Playwright runs headless in CI. For local debugging, pass `--headed` on the command line — no config change is needed.

---

## 4. Authentication Strategy

### Problem

OPNsense's UI requires a session cookie obtained via a POST to `/index.php` with form fields `userNameFieldName`, `passwordFieldName`, and `login`. The API key/secret used by the existing integration tests does not grant UI access; it is only valid for `/api/` endpoints.

A dedicated OPNsense user account for browser tests is required. This account must be created in the VM snapshot so it is available after every rollback.

**Credentials required (new secrets):**
| Secret name | Value |
|---|---|
| `OPNSENSE_UI_USER` | Username of the browser test account (e.g., `playwright`) |
| `OPNSENSE_UI_PASS` | Password for that account |

The `playwright` user must be in an ACL group that can access all Reticulum pages and the dashboard. The simplest approach is to add it to the built-in `admins` group on the VM snapshot.

### storageState pattern

Session cookies are short-lived and expensive to re-acquire on every test. The standard Playwright pattern is to log in once per test session, save the resulting browser storage state (cookies + localStorage) to a file, and load that file for all subsequent tests.

**Login flow (performed once per test session in a session-scoped fixture):**

1. Launch a browser context without any saved state.
2. Navigate to `https://<OPNSENSE_HOST>/`.
3. Fill `input[name="userNameFieldName"]` with `OPNSENSE_UI_USER`.
4. Fill `input[name="passwordFieldName"]` with `OPNSENSE_UI_PASS`.
5. Click the login button (`button[name="login"]` or `input[type="submit"]`).
6. Wait for navigation to complete and the OPNsense dashboard to appear (wait for selector `#mainmenu` or `div.page-content-head`).
7. Call `context.storage_state(path="tests/browser/fixtures/auth_state.json")`.
8. Close the context.

All subsequent `browser_context` fixtures load:

```python
context = browser.new_context(
    storage_state="tests/browser/fixtures/auth_state.json",
    ignore_https_errors=True,
)
```

The `auth_state.json` file is generated at the start of each CI run and is gitignored.

### API key auth for setup/teardown

Test data setup and teardown (creating/deleting interfaces, toggling services) uses the existing `OPNSENSE_API_KEY` / `OPNSENSE_API_SECRET` credentials via HTTP Basic auth with the `requests` library — the same pattern as the existing integration tests. This does not require browser interaction.

---

## 5. Fixture Architecture

All browser fixtures live in `browser/conftest.py`. Fixtures are layered: session-scoped expensive operations (login, API client) wrap function-scoped page instances.

### Fixture dependency graph

```
opnsense_api_client (session)
    └── used by: setup_interface, ensure_rnsd_running, etc.

authenticated_context (session)
    └── depends on: login_once (session)

authenticated_page (function)
    └── depends on: authenticated_context
    └── provides: a Page already logged in, navigated to base URL
```

### Fixture definitions

**`opnsense_api_client` (scope: session)**

A `requests.Session` pre-configured with:
- `auth=(OPNSENSE_API_KEY, OPNSENSE_API_SECRET)`
- `verify=False` (self-signed cert)
- base URL from `OPNSENSE_HOST`

Used in all setup/teardown helpers. Does not interact with the browser.

**`login_once` (scope: session)**

Performs the storageState login flow described in Section 4. Saves `auth_state.json`. Runs once per pytest session. Yields the path to the saved state file.

**`authenticated_context` (scope: session)**

Creates a Playwright `BrowserContext` from the saved `auth_state.json`:

```python
context = browser.new_context(
    storage_state=auth_state_path,
    ignore_https_errors=True,
)
```

Scope is session because creating a new context is expensive and the session cookie does not expire within a normal test run (~5 minutes).

**`authenticated_page` (scope: function)**

Opens a new `Page` from the session-scoped `authenticated_context`. Each test function gets its own page tab, preventing state bleed between tests. Yields the page object, then closes it after the test.

**`api_client` (scope: function)**

A thin wrapper around `opnsense_api_client` that provides convenience methods used in test setup/teardown:

| Method | HTTP call |
|---|---|
| `add_interface(data)` | `POST /api/reticulum/settings/addInterface` |
| `delete_interface(uuid)` | `POST /api/reticulum/settings/delInterface/<uuid>` |
| `list_interfaces()` | `GET /api/reticulum/settings/searchInterfaces` |
| `get_general()` | `GET /api/reticulum/rnsd/get` |
| `set_general(data)` | `POST /api/reticulum/rnsd/set` |
| `start_rnsd()` | `POST /api/reticulum/rnsd/start` |
| `stop_rnsd()` | `POST /api/reticulum/rnsd/stop` |
| `rnsd_status()` | `GET /api/reticulum/rnsd/status` |
| `start_lxmd()` | `POST /api/reticulum/lxmd/start` |
| `stop_lxmd()` | `POST /api/reticulum/lxmd/stop` |

**`ensure_rnsd_running` (scope: function)**

Calls `api_client.start_rnsd()` and polls `api_client.rnsd_status()` until status is `"running"` or 30 seconds elapses. Used as a fixture prerequisite for tests that require a live service (e.g., widget tests, log viewer tests with real log content).

**`ensure_rnsd_stopped` (scope: function)**

Mirror of `ensure_rnsd_running`. Used for tests that verify degraded-state UI behavior (G-517 rnsd dependency warning, W-604 widget degraded state).

**`clean_interfaces` (scope: function)**

Calls `api_client.list_interfaces()` and deletes any interface whose name starts with `"PW-"` (the test data prefix). Runs as a fixture teardown (yield-style), so it executes after the test regardless of pass/fail. Prevents test data accumulation across runs.

---

## 6. Page Object Model

Each page object wraps a Playwright `Page` instance and exposes intent-revealing methods rather than raw locators. Tests call page object methods; page objects contain all selectors.

### `BasePage`

**File:** `browser/pages/base_page.py`

**Responsibilities:**
- Navigation: `goto(path)` — calls `page.goto(base_url + path)` and waits for `networkidle`
- Alert handling: `get_success_alert()` → locator, `get_error_alert()` → locator
- Common UI: `wait_for_spinner_gone()` — waits for OPNsense's ajax spinner to disappear
- Breadcrumb: `page_title()` → text of the `h1` element

**Constructor:** `BasePage(page: Page, base_url: str)`

### `GeneralPage`

**File:** `browser/pages/general_page.py`

**Responsibilities:**
- `navigate()` — goto `/ui/reticulum/general`
- Form field accessors: `enable_transport_checkbox()`, `share_instance_checkbox()`, `shared_instance_port_input()`, `instance_control_port_input()`, `loglevel_select()`
- Actions: `save()` — clicks Save button, waits for alert or error
- Service bar: `service_status_text()`, `click_start()`, `click_stop()`, `click_restart()`
- Visibility helpers: `port_fields_visible()` → bool

### `InterfacesPage`

**File:** `browser/pages/interfaces_page.py`

**Responsibilities:**
- `navigate()` — goto `/ui/reticulum/interfaces`
- Grid: `grid_row_count()`, `get_row_by_name(name)` → row locator, `click_add()`, `click_edit(name)`, `click_delete(name)`, `confirm_delete()`
- Modal: `modal_visible()` → bool, `set_name(name)`, `set_type(type_value)`, `save_modal()`, `cancel_modal()`
- Type-specific field accessors per tab:
  - TCP/UDP: `set_listen_port(port)`, `set_target_host(host)`, `set_target_port(port)`
  - RNode: `set_port(port)`, `set_frequency(freq)`, `set_bandwidth(bw)`, `set_txpower(pwr)`, `set_spreading_factor(sf)`, `set_coding_rate(cr)`
  - Serial/KISS/AX.25: `set_port(port)`, `set_speed(speed)`
- Visibility helper: `fields_visible_for_type(type_value)` → set of visible field names

**Note:** The type-visibility system in `interfaces.volt` uses CSS classes (`type-tcp`, `type-rnode`, etc.) to show/hide fields. The page object must query visibility via `is_visible()` rather than DOM presence.

### `LxmfPage`

**File:** `browser/pages/lxmf_page.py`

**Responsibilities:**
- `navigate()` — goto `/ui/reticulum/lxmf`
- Dependency warning: `rnsd_warning_visible()` → bool
- Propagation section: `enable_node_checkbox()`, `propagation_fields_visible()` → bool
- Field accessors for key fields: `static_peers_input()`, `from_static_only_checkbox()`
- Validation: `static_only_warning_visible()` → bool
- Service bars: `rnsd_status_text()`, `lxmd_status_text()`

### `LogsPage`

**File:** `browser/pages/logs_page.py`

**Responsibilities:**
- `navigate()` — goto `/ui/reticulum/logs`
- Tab switching: `click_rnsd_tab()`, `click_lxmd_tab()`
- Log content: `log_line_count()`, `log_lines()` → list of strings
- Filters: `set_severity_filter(level)`, `set_keyword_filter(keyword)`
- Auto-refresh: `click_auto_refresh_toggle()`, `auto_refresh_active()` → bool

### `DashboardPage`

**File:** `browser/pages/dashboard_page.py`

**Responsibilities:**
- `navigate()` — goto `/ui/dashboard/index`
- Widget management: `open_widget_picker()`, `widget_in_picker(name)` → bool, `add_widget(name)`
- Widget inspection (after adding): `widget_visible(name)` → bool, `rnsd_status_in_widget()` → str, `lxmd_status_in_widget()` → str, `interface_rows_in_widget()` → list of dicts
- Responsive: `widget_column_visible(column_name)` → bool

---

## 7. Test Data Management

### Principle

Tests must not depend on pre-existing data in the VM. Every test that needs an interface, a specific setting value, or a particular service state must create that state via the API in a fixture, and tear it down after the test.

The snapshot restore that runs at the top of every CI job ensures a clean base, but tests within the same job can interfere with each other. Setup/teardown fixtures prevent this.

### Interface test data

Interfaces created by browser tests use the name prefix `"PW-"` (e.g., `"PW-TCP-Test"`, `"PW-RNode-Test"`). The `clean_interfaces` fixture (Section 5) deletes all interfaces whose names start with `"PW-"` after each test.

**Seed data for read-only tests:**

Some tests (e.g., G-508 "grid loads with configured interfaces") need at least one interface to exist before the page is loaded. These tests use a session-scoped `seed_one_interface` fixture that:

1. Creates a minimal TCPServerInterface via `api_client.add_interface()` using values from `fixtures/interfaces_seed.json`.
2. Yields.
3. Deletes it by UUID after the session ends.

`fixtures/interfaces_seed.json` contains one interface definition:

```json
{
  "name": "PW-Seed-TCP",
  "type": "TCPServerInterface",
  "listen_port": "9999",
  "enabled": "1"
}
```

### Settings test data

Tests that modify General Settings (`/api/reticulum/rnsd/set`) must restore the original values after the test. Use a function-scoped fixture that:

1. Calls `api_client.get_general()` and saves the response as `original_settings`.
2. Yields.
3. Calls `api_client.set_general(original_settings)` to restore.

### Service state

Tests in `test_PW_general.py` and `test_PW_lxmf.py` that start or stop services use `ensure_rnsd_running` / `ensure_rnsd_stopped` (Section 5). These fixtures do not restore service state after the test. The test file must order tests so that any test leaving rnsd in a stopped state is followed by a test that either expects it stopped or uses `ensure_rnsd_running` itself.

In practice: tests that stop rnsd are tagged with a marker `@pytest.mark.requires_stopped_rnsd` and grouped at the end of the file so they do not cascade into tests that need rnsd running.

---

## 8. CI Integration

### New job: `browser-test`

Add a new job to the existing `integration-test.yml` workflow. The new job runs **after** the existing `integration-test` job (depends on its success), on the same self-hosted runner, while the VM is still running.

**Reason for sequencing:** The existing job deploys the plugin, runs pytest, and runs the API shell tests. The browser job adds Playwright tests on top of the already-deployed VM. Running them in the same workflow run reuses the Proxmox snapshot restore and avoids booting the VM twice.

**Ordering in the workflow:**

```yaml
jobs:
  integration-test:
    # ... existing job (unchanged) ...

  browser-test:
    name: OPNsense Browser Tests (Playwright)
    needs: integration-test
    runs-on: [self-hosted, opnsense-test]
    timeout-minutes: 30
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: false

      - name: Install browser test dependencies
        run: |
          python3 -m venv .venv-browser
          .venv-browser/bin/pip install --upgrade pip
          .venv-browser/bin/pip install -r os-reticulum/tests/requirements-browser.txt

      - name: Install Chromium
        run: .venv-browser/bin/playwright install chromium

      - name: Run Playwright tests
        env:
          OPNSENSE_HOST: ${{ secrets.OPNSENSE_HOST }}
          OPNSENSE_API_KEY: ${{ secrets.OPNSENSE_API_KEY }}
          OPNSENSE_API_SECRET: ${{ secrets.OPNSENSE_API_SECRET }}
          OPNSENSE_UI_USER: ${{ secrets.OPNSENSE_UI_USER }}
          OPNSENSE_UI_PASS: ${{ secrets.OPNSENSE_UI_PASS }}
        run: |
          .venv-browser/bin/pytest os-reticulum/tests/browser/ \
            -v --tb=short -m browser \
            --junit-xml=browser-test-results.xml

      - name: Upload Playwright artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: browser-test-results-${{ github.run_number }}
          path: |
            browser-test-results.xml
            playwright-report/
            test-results/
```

### Headed vs. headless

Playwright runs **headless** in CI by default (pytest-playwright default). No `--headed` flag is passed in the workflow.

For local debugging against a live VM, run:

```sh
.venv-browser/bin/pytest os-reticulum/tests/browser/ -m browser --headed -v
```

### Playwright browser installation on the self-hosted runner

The runner must have the system libraries that Chromium depends on. On FreeBSD (if the runner itself runs FreeBSD), use `playwright install-deps chromium`. On a Linux runner host (more common for GitHub Actions self-hosted), `playwright install-deps` installs the required apt packages automatically.

The `playwright install chromium` step in the workflow downloads the browser binary into the runner's local Playwright cache (`~/.cache/ms-playwright/`). This is persistent across runs on a self-hosted runner, so subsequent runs skip the download if the version has not changed.

---

## 9. Environment Configuration

### Self-signed certificate

OPNsense uses a self-signed TLS certificate by default. All browser contexts must be created with `ignore_https_errors=True`. This is set in the `authenticated_context` fixture and must not be overridden in individual tests.

In `requests`-based API calls, `verify=False` is set on the session in `opnsense_api_client`.

**Do not** install a trusted certificate in the VM snapshot. The purpose of these tests is to validate UI behavior on a stock OPNsense deployment.

### Timeouts

All timeouts are defined in `browser/conftest.py` as module-level constants so they can be adjusted in one place:

| Constant | Value | Used for |
|---|---|---|
| `PAGE_LOAD_TIMEOUT` | 30 000 ms | `page.goto()` navigation |
| `ELEMENT_TIMEOUT` | 10 000 ms | `locator.wait_for()` and assertions |
| `SERVICE_START_TIMEOUT` | 30 000 ms | Polling `rnsd_status()` in fixtures |
| `AJAX_SPINNER_TIMEOUT` | 15 000 ms | `wait_for_spinner_gone()` |

Pass `PAGE_LOAD_TIMEOUT` to `page.set_default_navigation_timeout()` and `ELEMENT_TIMEOUT` to `page.set_default_timeout()` in the `authenticated_page` fixture immediately after creating the page.

### Retry strategy

pytest-playwright does not retry failed tests by default. Do not add automatic retries. Playwright assertions (`expect(locator).to_be_visible()`) already have built-in polling with `ELEMENT_TIMEOUT` as the deadline.

If a test is flaky due to an OPNsense AJAX timing issue, the correct fix is to add an explicit wait for the relevant element or network request in the page object — not to add retries.

### Screenshot on failure

Configure Playwright to capture a screenshot on test failure by setting the `--screenshot=only-on-failure` flag in the CI pytest command, and `--output=test-results/` for the artifact directory. This produces per-test PNG files that are included in the uploaded CI artifact.

Updated CI run command:

```sh
.venv-browser/bin/pytest os-reticulum/tests/browser/ \
  -v --tb=short -m browser \
  --screenshot=only-on-failure \
  --output=test-results/ \
  --junit-xml=browser-test-results.xml
```

---

## 10. Naming Conventions

### Test ID prefix: `PW-`

Browser tests use the `PW-` prefix, consistent with the existing series:

| Prefix | Series | Category |
|---|---|---|
| `T-` | 101–112 | Template output |
| `M-` | 201–209 | Model validation |
| `A-` | 301–309 | API endpoints |
| `S-` | 401–407 | Service lifecycle |
| `G-` | 501–525 | GUI (manual checklist; superseded by PW-) |
| `W-` | 601–606 | Widget (manual checklist; superseded by PW-) |
| `X-` | 701–710 | Security |
| `E-` | 901–910 | Edge cases |
| **`PW-`** | **101–599** | **Browser automation (Playwright)** |

The `PW-` range is subdivided by page, mirroring the G-/W- manual checklist structure:

| Range | Page |
|---|---|
| PW-101 – PW-120 | General Settings |
| PW-201 – PW-240 | Interfaces |
| PW-301 – PW-320 | Propagation Node (LXMF) |
| PW-401 – PW-410 | Log Viewer |
| PW-501 – PW-510 | Dashboard widget |

Gaps are intentional: leave room for new tests without renumbering. IDs 101–120 allocates 20 slots for General Settings, which has 7 manual tests; the extra capacity is for expanded coverage later.

### Test function names

Follow the pattern used in the existing integration tests:

```
test_<ID>_<short_description>
```

Examples:
- `test_PW101_general_page_loads_without_js_errors`
- `test_PW201_interfaces_grid_loads`
- `test_PW211_add_tcpserver_interface_modal`
- `test_PW301_rnsd_dependency_warning_visible_when_stopped`

### Test file names

```
test_PW_<page>.py
```

Files: `test_PW_general.py`, `test_PW_interfaces.py`, `test_PW_lxmf.py`, `test_PW_logs.py`, `test_PW_widget.py`

### Class names

Page object classes use PascalCase with `Page` suffix:

- `BasePage`
- `GeneralPage`
- `InterfacesPage`
- `LxmfPage`
- `LogsPage`
- `DashboardPage`

Fixture module-level helper classes (e.g., API client wrapper) use PascalCase with the suffix `Client` or `Helper`:

- `OPNsenseApiClient`

### pytest markers

All browser tests are decorated with `@pytest.mark.browser`. Tests that additionally require rnsd to be stopped use `@pytest.mark.requires_stopped_rnsd`. These markers are registered in `pytest.ini`.

---

## 11. Relationship to Existing G-/W- Manual Checklist

The Playwright tests in `tests/browser/` are intended to automate the G-501–G-525 and W-601–W-606 manual checklist in `tests/gui/gui_checklist.md`. When a manual test is fully automated, the checklist row can be annotated with the corresponding `PW-` ID.

The manual checklist is not deleted. It remains useful for:
- Smoke-testing on a fresh VM before CI is set up
- Exploratory testing of visual layout issues that Playwright assertions cannot catch
- Cross-referencing when a PW- test fails (the checklist steps describe the exact manual reproduction)

---

## 12. New Secrets Required

The following GitHub Actions secrets must be added before the `browser-test` CI job can run:

| Secret | Description |
|---|---|
| `OPNSENSE_UI_USER` | Username of the Playwright test account on the OPNsense VM snapshot |
| `OPNSENSE_UI_PASS` | Password for that account |

The existing secrets (`OPNSENSE_HOST`, `OPNSENSE_API_KEY`, `OPNSENSE_API_SECRET`, `OPNSENSE_SSH_KEY`, Proxmox secrets) are reused unchanged.

The `playwright` user account must be provisioned in the VM snapshot used for CI. It should be added to the `admins` group so it can access all Reticulum menu items without needing a custom ACL group.

---

## Known Open Questions

These items are not resolved in this spec and must be decided before implementation:

1. **OPNsense login form field names**: The field names `userNameFieldName` and `passwordFieldName` are taken from OPNsense source convention. They should be verified by inspecting the actual HTML of the login page on the target OPNsense version before writing the login fixture.

2. **Session cookie lifetime**: OPNsense session cookies expire after a configurable idle timeout (default varies by version). If the browser test suite takes longer than the session timeout, the `authenticated_context` fixture will need to re-login mid-session. The current spec assumes the suite completes within the default timeout.

3. **Dashboard widget add selector**: The widget picker UI in OPNsense varies by version. The exact CSS selector for the "Add Widget" button and the widget list must be verified on the target OPNsense version.

4. **PW user creation in CI deploy step**: The `Deploy plugin to OPNsense` step in `integration-test.yml` provisions the `reticulum` system user. A corresponding step to create the `OPNSENSE_UI_USER` account should be added to the same step — or the user can be baked into the VM snapshot. The spec does not prescribe which; this is an implementation decision.
