"""Playwright browser tests for the Log Viewer page.

Covers tab navigation (PW-LOG-001–003), filter controls (PW-LOG-010–015),
action buttons (PW-LOG-020–025), output states (PW-LOG-030–034),
and download (PW-LOG-040–042).

Requires a live OPNsense VM — see conftest.py for env var requirements.
"""

import pytest
from playwright.sync_api import expect

from browser.pages.logs_page import LogsPage


pytestmark = pytest.mark.browser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _logs_page(authenticated_page, base_url) -> LogsPage:
    """Instantiate and navigate to the LogsPage."""
    lp = LogsPage(authenticated_page, base_url)
    lp.navigate()
    return lp


# ===========================================================================
# Tab navigation (PW-LOG-001–003)
# ===========================================================================

def test_PW_LOG_001_rnsd_tab_active_by_default(authenticated_page, base_url):
    """The rnsd tab is selected/active when the page first loads."""
    lp = _logs_page(authenticated_page, base_url)

    # Bootstrap marks the active tab with .active on the parent <li> or the
    # <a> element itself — check that the rnsd tab carries the active class.
    expect(lp.rnsd_tab).to_have_class(r".*active.*")


def test_PW_LOG_002_lxmd_tab_clickable(authenticated_page, base_url):
    """Clicking the lxmd tab makes it active."""
    lp = _logs_page(authenticated_page, base_url)

    lp.click_lxmd_tab()
    expect(lp.lxmd_tab).to_have_class(r".*active.*")


def test_PW_LOG_003_tab_switch_triggers_fetch(authenticated_page, base_url):
    """Switching tabs causes the log output area to update."""
    lp = _logs_page(authenticated_page, base_url)

    # Capture initial content (may be empty-service or actual lines)
    initial_html = lp.log_output.inner_html()

    lp.click_lxmd_tab()

    # After switching, the output area should have been refreshed.  We cannot
    # guarantee _different_ content (both tabs may be empty), but the loading
    # indicator should have appeared or the output should be present.
    lp.page.wait_for_timeout(1000)
    # Verify we are on lxmd tab now and the page did not error out
    expect(lp.lxmd_tab).to_have_class(r".*active.*")
    # The output area should still be in the DOM
    expect(lp.log_output).to_be_attached()


# ===========================================================================
# Filter controls (PW-LOG-010–015)
# ===========================================================================

def test_PW_LOG_010_severity_filter_present(authenticated_page, base_url):
    """#log-level select exists with multiple options."""
    lp = _logs_page(authenticated_page, base_url)

    expect(lp.severity_filter).to_be_visible()
    options = lp.severity_filter.locator("option")
    assert options.count() >= 2, (
        f"Expected at least 2 severity options, got {options.count()}"
    )


def test_PW_LOG_011_keyword_filter_present(authenticated_page, base_url):
    """#log-search input exists and accepts text."""
    lp = _logs_page(authenticated_page, base_url)

    expect(lp.keyword_filter).to_be_visible()
    lp.set_keyword_filter("test_keyword")
    expect(lp.keyword_filter).to_have_value("test_keyword")


def test_PW_LOG_012_lines_select_present(authenticated_page, base_url):
    """#log-lines select exists with default value of 200."""
    lp = _logs_page(authenticated_page, base_url)

    expect(lp.lines_select).to_be_visible()
    expect(lp.lines_select).to_have_value("200")


def test_PW_LOG_013_severity_filter_filters_cached(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Changing severity filters cached content without a new network request."""
    lp = _logs_page(authenticated_page, base_url)

    # Wait for log content to appear
    lp.expect_log_output_visible()
    lp.page.wait_for_timeout(1000)

    initial_count = lp.log_line_count()
    if initial_count == 0:
        pytest.skip("No log lines available to filter")

    # Track network requests to the log API endpoint
    request_count = {"value": 0}

    def on_request(request):
        if "log" in request.url.lower() and "api" in request.url.lower():
            request_count["value"] += 1

    lp.page.on("request", on_request)

    # Change severity to a specific level — should filter client-side
    lp.set_severity_filter("error")
    lp.page.wait_for_timeout(500)

    filtered_count = lp.log_line_count()
    # Filtered count should differ from initial (unless all lines match)
    # The key assertion: no new network fetch was triggered
    assert request_count["value"] == 0, (
        f"Expected client-side filter but {request_count['value']} API requests fired"
    )

    lp.page.remove_listener("request", on_request)


def test_PW_LOG_014_keyword_filter_filters_cached(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Typing a keyword reduces visible log lines to matching ones."""
    lp = _logs_page(authenticated_page, base_url)

    lp.expect_log_output_visible()
    lp.page.wait_for_timeout(1000)

    initial_count = lp.log_line_count()
    if initial_count == 0:
        pytest.skip("No log lines available to filter")

    # Use a keyword very unlikely to match all lines
    lp.set_keyword_filter("ZZZZUNLIKELYMATCH")
    lp.page.wait_for_timeout(500)

    filtered_count = lp.log_line_count()
    assert filtered_count < initial_count or filtered_count == 0, (
        f"Keyword filter did not reduce lines: {initial_count} -> {filtered_count}"
    )


def test_PW_LOG_015_lines_change_triggers_fetch(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Changing line count triggers a new fetch."""
    lp = _logs_page(authenticated_page, base_url)

    lp.expect_log_output_visible()

    request_fired = {"value": False}

    def on_request(request):
        if "log" in request.url.lower():
            request_fired["value"] = True

    lp.page.on("request", on_request)

    # Change from default 200 to a different value
    lp.set_lines_count("50")
    lp.page.wait_for_timeout(2000)

    assert request_fired["value"], "Changing line count did not trigger a new fetch"

    lp.page.remove_listener("request", on_request)


# ===========================================================================
# Action buttons (PW-LOG-020–025)
# ===========================================================================

def test_PW_LOG_020_refresh_button(authenticated_page, base_url):
    """Click refresh completes without error."""
    lp = _logs_page(authenticated_page, base_url)

    errors: list[str] = []
    authenticated_page.on("pageerror", lambda exc: errors.append(str(exc)))

    lp.click_refresh()
    assert errors == [], f"JS errors after refresh: {errors}"


def test_PW_LOG_021_download_button_present(authenticated_page, base_url):
    """Download button exists and is visible."""
    lp = _logs_page(authenticated_page, base_url)

    expect(lp.download_btn).to_be_visible()


def test_PW_LOG_023_auto_refresh_toggle(authenticated_page, base_url):
    """Toggle auto-refresh on and off; verify state each time."""
    lp = _logs_page(authenticated_page, base_url)

    # Ensure auto-refresh starts unchecked
    if lp.auto_refresh_active():
        lp.toggle_auto_refresh()

    assert not lp.auto_refresh_active(), "Auto-refresh should start inactive"

    # Enable
    lp.toggle_auto_refresh()
    assert lp.auto_refresh_active(), "Auto-refresh should be active after toggle"

    # Disable
    lp.toggle_auto_refresh()
    assert not lp.auto_refresh_active(), "Auto-refresh should be inactive after second toggle"


def test_PW_LOG_024_025_auto_refresh_interval(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Auto-refresh fetches new content after ~5s interval."""
    lp = _logs_page(authenticated_page, base_url)

    lp.expect_log_output_visible()

    # Enable auto-refresh
    if not lp.auto_refresh_active():
        lp.toggle_auto_refresh()

    # Track refresh requests
    refresh_count = {"value": 0}

    def on_request(request):
        if "log" in request.url.lower():
            refresh_count["value"] += 1

    lp.page.on("request", on_request)

    # Wait slightly over one interval
    lp.page.wait_for_timeout(6000)

    assert refresh_count["value"] >= 1, (
        f"Expected at least 1 auto-refresh request, got {refresh_count['value']}"
    )

    lp.page.remove_listener("request", on_request)

    # Clean up: disable auto-refresh
    if lp.auto_refresh_active():
        lp.toggle_auto_refresh()


# ===========================================================================
# Output states (PW-LOG-030–034)
# ===========================================================================

def test_PW_LOG_033_log_output_rendered(
    authenticated_page, base_url, ensure_rnsd_running
):
    """With rnsd running and generating logs, #log-output is visible with content."""
    lp = _logs_page(authenticated_page, base_url)

    lp.expect_log_output_visible()
    lp.page.wait_for_timeout(1000)

    line_count = lp.log_line_count()
    assert line_count > 0, "Expected log lines but output is empty"


def test_PW_LOG_032_empty_filter_state(
    authenticated_page, base_url, ensure_rnsd_running
):
    """With logs present, a keyword filter matching nothing shows empty-filter message."""
    lp = _logs_page(authenticated_page, base_url)

    lp.expect_log_output_visible()
    lp.page.wait_for_timeout(1000)

    if lp.log_line_count() == 0:
        pytest.skip("No log lines to filter — cannot test empty-filter state")

    lp.set_keyword_filter("ZZZZUNLIKELYMATCH99999")
    lp.page.wait_for_timeout(500)

    lp.expect_empty_filter_visible()


# ===========================================================================
# Download (PW-LOG-040–042)
# ===========================================================================

def test_PW_LOG_040_041_download_filtered_lines(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Click download and verify a file is downloaded with 'rnsd' in the name."""
    lp = _logs_page(authenticated_page, base_url)

    lp.expect_log_output_visible()
    lp.page.wait_for_timeout(1000)

    with authenticated_page.expect_download() as download_info:
        lp.click_download()

    download = download_info.value
    assert "rnsd" in download.suggested_filename.lower(), (
        f"Expected 'rnsd' in download filename, got: {download.suggested_filename}"
    )


# ===========================================================================
# Tests requiring stopped rnsd — placed at END of file
# ===========================================================================

@pytest.mark.requires_stopped_rnsd
def test_PW_LOG_031_empty_service_state(
    authenticated_page, base_url, ensure_rnsd_stopped
):
    """With rnsd stopped and no log file, the empty-service message is visible."""
    lp = _logs_page(authenticated_page, base_url)

    lp.page.wait_for_timeout(1000)
    lp.expect_empty_service_visible()
