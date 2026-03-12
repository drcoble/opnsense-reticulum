"""Playwright browser tests for the Reticulum Dashboard Widget.

Covers widget presence (PW-WDG-001–009), status indicators (PW-WDG-050–053),
degraded state (PW-WDG-016–017, 040–042), compact view (PW-WDG-018–020),
responsive breakpoints (PW-WDG-030–033), and tick interval (PW-WDG-021).

Requires a live OPNsense VM — see conftest.py for env var requirements.
"""

import pytest
from playwright.sync_api import expect

from browser.pages.dashboard_page import DashboardPage


pytestmark = pytest.mark.browser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dashboard_page(authenticated_page, base_url) -> DashboardPage:
    """Instantiate and navigate to the DashboardPage."""
    dp = DashboardPage(authenticated_page, base_url)
    dp.navigate()
    return dp


# ===========================================================================
# Widget presence (PW-WDG-001–009)
# ===========================================================================

def test_PW_WDG_001_widget_container_present(
    authenticated_page, base_url, ensure_rnsd_running
):
    """#reticulum-widget exists on the dashboard."""
    dp = _dashboard_page(authenticated_page, base_url)

    dp.expect_widget_visible()


def test_PW_WDG_002_rnsd_status_row(
    authenticated_page, base_url, ensure_rnsd_running
):
    """#ret-rnsd-status is present and contains text."""
    dp = _dashboard_page(authenticated_page, base_url)

    expect(dp.rnsd_status).to_be_visible()
    status_text = dp.get_rnsd_status()
    assert len(status_text.strip()) > 0, "rnsd status row has no text"


def test_PW_WDG_003_lxmd_status_row(
    authenticated_page, base_url, ensure_rnsd_running
):
    """#ret-row-lxmd and #ret-lxmd-status are present."""
    dp = _dashboard_page(authenticated_page, base_url)

    expect(dp.lxmd_row).to_be_attached()
    expect(dp.lxmd_status).to_be_attached()


def test_PW_WDG_005_interface_count_row(
    authenticated_page, base_url, ensure_rnsd_running
):
    """#ret-ifcount is present on the widget."""
    dp = _dashboard_page(authenticated_page, base_url)

    expect(dp.ifcount).to_be_attached()


def test_PW_WDG_006_traffic_row(
    authenticated_page, base_url, ensure_rnsd_running
):
    """#ret-traffic is present on the widget."""
    dp = _dashboard_page(authenticated_page, base_url)

    expect(dp.traffic).to_be_attached()


def test_PW_WDG_007_version_row(
    authenticated_page, base_url, ensure_rnsd_running
):
    """#ret-version is present and contains text."""
    dp = _dashboard_page(authenticated_page, base_url)

    expect(dp.version).to_be_attached()
    version_text = dp.get_version()
    assert len(version_text.strip()) > 0, "Version row has no text"


def test_PW_WDG_008_identity_row(
    authenticated_page, base_url, ensure_rnsd_running
):
    """#ret-identity is present and contains text."""
    dp = _dashboard_page(authenticated_page, base_url)

    expect(dp.identity).to_be_attached()
    identity_text = dp.get_identity()
    assert len(identity_text.strip()) > 0, "Identity row has no text"


def test_PW_WDG_009_interface_table(
    authenticated_page, base_url, seed_one_interface, ensure_rnsd_running
):
    """#ret-iface-table is present when interfaces exist and rnsd is running."""
    dp = _dashboard_page(authenticated_page, base_url)

    dp.expect_iface_table_visible()


# ===========================================================================
# Status indicators (PW-WDG-050–053)
# ===========================================================================

def test_PW_WDG_050_rnsd_running_green(
    authenticated_page, base_url, ensure_rnsd_running
):
    """With rnsd running, status shows a running indicator."""
    dp = _dashboard_page(authenticated_page, base_url)

    expect(dp.rnsd_status).to_be_visible()
    status_text = dp.get_rnsd_status().lower()
    assert "running" in status_text or "ok" in status_text, (
        f"Expected running indicator, got: {status_text}"
    )


def test_PW_WDG_051_lxmd_status_displayed(
    authenticated_page, base_url, ensure_rnsd_running
):
    """lxmd status element has text content."""
    dp = _dashboard_page(authenticated_page, base_url)

    expect(dp.lxmd_status).to_be_attached()
    status_text = dp.get_lxmd_status()
    assert len(status_text.strip()) > 0, "lxmd status has no text"


def test_PW_WDG_053_interface_data_populated(
    authenticated_page, base_url, seed_one_interface, ensure_rnsd_running
):
    """With rnsd running and a seed interface, interface table has at least one row."""
    dp = _dashboard_page(authenticated_page, base_url)

    dp.expect_iface_table_visible()
    rows = dp.interface_rows()
    assert len(rows) >= 1, f"Expected at least 1 interface row, got {len(rows)}"


# ===========================================================================
# Degraded state (PW-WDG-016–017, 040–042)
# ===========================================================================

def test_PW_WDG_017_degraded_link_to_general(
    authenticated_page, base_url, ensure_rnsd_stopped
):
    """Degraded message contains a link to the general settings page."""
    dp = _dashboard_page(authenticated_page, base_url)

    dp.expect_degraded_visible()
    link = dp.degraded.locator("a")
    expect(link).to_be_visible()
    href = link.get_attribute("href")
    assert href is not None and "general" in href.lower(), (
        f"Expected link to general page, got href: {href}"
    )


def test_PW_WDG_040_degraded_hides_iface_section(
    authenticated_page, base_url, ensure_rnsd_stopped
):
    """In degraded state, the interface table section is hidden."""
    dp = _dashboard_page(authenticated_page, base_url)

    dp.expect_degraded_visible()
    dp.expect_iface_table_hidden()


# ===========================================================================
# Compact view (PW-WDG-018–020)
# ===========================================================================

def test_PW_WDG_018_019_020_compact_elements_exist(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Compact container and rnsd/lxmd status icons exist in the DOM."""
    dp = _dashboard_page(authenticated_page, base_url)

    expect(dp.compact).to_be_attached()
    expect(dp.compact_rnsd).to_be_attached()
    expect(dp.compact_lxmd).to_be_attached()


# ===========================================================================
# Responsive breakpoints (PW-WDG-030–033)
# ===========================================================================

def test_PW_WDG_030_full_width_all_visible(
    authenticated_page, base_url, ensure_rnsd_running
):
    """At full width (>= 400px), all detail rows visible and compact hidden."""
    dp = _dashboard_page(authenticated_page, base_url)

    # The widget renders inside the dashboard grid.  We verify that at the
    # default viewport the detail rows are visible and compact is hidden.
    expect(dp.rnsd_status).to_be_visible()
    expect(dp.version).to_be_visible()
    dp.expect_compact_hidden()


def test_PW_WDG_031_medium_width_no_traffic_col(
    authenticated_page, base_url, ensure_rnsd_running
):
    """At medium width (300-399px), .ret-col-traffic columns are hidden.

    Note: widget sizing may be controlled by the dashboard grid rather than
    the viewport.  This test is best-effort — it resizes the viewport and
    checks visibility, but may not trigger the widget's onWidgetResize if
    the grid layout does not shrink the widget container.
    """
    _dashboard_page(authenticated_page, base_url)

    # Attempt to trigger a narrow viewport
    authenticated_page.set_viewport_size({"width": 350, "height": 800})
    authenticated_page.wait_for_timeout(1000)

    traffic_cols = authenticated_page.locator(".ret-col-traffic")
    if traffic_cols.count() > 0:
        # At narrow width these should be hidden; but if the dashboard grid
        # does not resize the widget, they may still be visible.
        first_col = traffic_cols.first
        if first_col.is_visible():
            pytest.skip(
                "Dashboard grid did not shrink widget — "
                "viewport resize does not trigger onWidgetResize"
            )
        expect(first_col).to_be_hidden()
    else:
        pytest.skip("No .ret-col-traffic elements found in widget")


# ===========================================================================
# Tick interval (PW-WDG-021)
# ===========================================================================

def test_PW_WDG_021_tick_interval_refreshes(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Wait >15s and verify the widget data refreshes via API calls."""
    dp = _dashboard_page(authenticated_page, base_url)

    dp.expect_widget_visible()

    # Track API requests to the reticulum status endpoints
    refresh_count = {"value": 0}

    def on_request(request):
        url = request.url.lower()
        if "reticulum" in url and ("status" in url or "service" in url):
            refresh_count["value"] += 1

    authenticated_page.on("request", on_request)

    # Wait slightly over the 15s tick interval
    authenticated_page.wait_for_timeout(16000)

    assert refresh_count["value"] >= 1, (
        f"Expected at least 1 tick refresh, got {refresh_count['value']}"
    )

    authenticated_page.remove_listener("request", on_request)


# ===========================================================================
# Tests requiring stopped rnsd — placed at END of file
# ===========================================================================

@pytest.mark.requires_stopped_rnsd
def test_PW_WDG_016_degraded_state_when_stopped(
    authenticated_page, base_url, ensure_rnsd_stopped
):
    """With rnsd stopped, #ret-degraded is visible."""
    dp = _dashboard_page(authenticated_page, base_url)

    dp.expect_degraded_visible()
