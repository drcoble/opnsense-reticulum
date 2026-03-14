"""Playwright browser tests for the LXMF Propagation Node page.

Covers dual service bar (PW-LXM-001-011), tab navigation (020-027),
General tab (030-034), Propagation tab (040-050), Sync size validation
(046-048), Stamp Costs tab (060-062), Peering tab (070-075), ACL tab
(080-084), Logging tab (090-093), and form footer (095-097).

Requires a live OPNsense VM -- see conftest.py for env var requirements.
"""

import pytest
from playwright.sync_api import expect

from browser.pages.lxmf_page import LxmfPage


pytestmark = pytest.mark.browser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lxmf_page(authenticated_page, base_url) -> LxmfPage:
    """Instantiate and navigate to the LxmfPage."""
    lp = LxmfPage(authenticated_page, base_url)
    lp.navigate()
    return lp


def _enable_propagation(lp: LxmfPage) -> None:
    """Navigate to the propagation tab and enable the propagation node."""
    lp.select_tab("propagation")
    lp.set_enable_node(True)


# ===========================================================================
# Dual service bar (PW-LXM-001-011)
# ===========================================================================

def test_PW_LXM_001_rnsd_status_badge_present(
    authenticated_page, base_url, ensure_rnsd_running
):
    """#rnsd-status-badge exists and shows text."""
    lp = _lxmf_page(authenticated_page, base_url)

    expect(lp.rnsd_status_badge).to_be_visible()
    text = lp.get_rnsd_status()
    assert len(text.strip()) > 0, "rnsd status badge is empty"


def test_PW_LXM_002_link_to_general_page(authenticated_page, base_url):
    """At least one link with href /ui/reticulum/general exists on the page."""
    _lxmf_page(authenticated_page, base_url)

    links = authenticated_page.locator('a[href="/ui/reticulum/general"]')
    assert links.count() >= 1, "No link to /ui/reticulum/general found on LXMF page"


def test_PW_LXM_003_lxmd_start_button(authenticated_page, base_url):
    """Start button is present."""
    lp = _lxmf_page(authenticated_page, base_url)

    expect(lp.lxmd_btn_start).to_be_visible()


def test_PW_LXM_004_lxmd_stop_button(authenticated_page, base_url):
    """Stop button is present."""
    lp = _lxmf_page(authenticated_page, base_url)

    expect(lp.lxmd_btn_stop).to_be_visible()


def test_PW_LXM_005_lxmd_restart_button(authenticated_page, base_url):
    """Restart button is present."""
    lp = _lxmf_page(authenticated_page, base_url)

    expect(lp.lxmd_btn_restart).to_be_visible()


def test_PW_LXM_006_lxmd_status_badge_present(authenticated_page, base_url):
    """#lxmd-status-badge exists."""
    lp = _lxmf_page(authenticated_page, base_url)

    expect(lp.lxmd_status_badge).to_be_visible()


def test_PW_LXM_011_rnsd_warning_hidden_when_running(
    authenticated_page, base_url, ensure_rnsd_running
):
    """With rnsd running, #rnsd-warning is hidden."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.expect_rnsd_warning_hidden()


# ===========================================================================
# Tab navigation (PW-LXM-020-027)
# ===========================================================================

def test_PW_LXM_020_025_all_tabs_navigable(authenticated_page, base_url):
    """Click each of 6 tabs, verify the pane becomes active.

    Costs and Peering are propagation-dependent, so enable propagation first.
    """
    lp = _lxmf_page(authenticated_page, base_url)

    # General, Propagation, Logging are always visible
    for tab_name in ("general", "propagation", "logging"):
        lp.select_tab(tab_name)

    # Enable propagation to reveal Costs, Peering, ACL tabs
    lp.select_tab("propagation")
    lp.set_enable_node(True)

    for tab_name in ("costs", "peering", "acl"):
        lp.select_tab(tab_name)


def test_PW_LXM_026_propagation_dep_tabs_visible_when_enabled(
    authenticated_page, base_url
):
    """Checking enable_node makes Costs and Peering tabs appear."""
    lp = _lxmf_page(authenticated_page, base_url)

    _enable_propagation(lp)
    lp.expect_propagation_tabs_visible()


def test_PW_LXM_027_propagation_dep_tabs_hidden_when_disabled(
    authenticated_page, base_url
):
    """Unchecking enable_node hides Costs and Peering tabs."""
    lp = _lxmf_page(authenticated_page, base_url)

    # First enable, then disable to confirm they hide
    lp.select_tab("propagation")
    lp.set_enable_node(True)
    lp.expect_propagation_tabs_visible()

    lp.set_enable_node(False)
    lp.expect_propagation_tabs_hidden()


# ===========================================================================
# General tab (PW-LXM-030-034)
# ===========================================================================

def test_PW_LXM_030_lxmf_enabled_checkbox(authenticated_page, base_url):
    """LXMF enabled checkbox is present and toggleable."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("general")
    expect(lp.lxmf_enabled).to_be_visible()
    expect(lp.lxmf_enabled).to_be_enabled()


def test_PW_LXM_031_display_name_input(authenticated_page, base_url):
    """Display name input field is present."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("general")
    expect(lp.display_name).to_be_visible()


def test_PW_LXM_032_announce_at_start_checkbox(authenticated_page, base_url):
    """LXMF announce at start checkbox is present."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("general")
    expect(lp.lxmf_announce_at_start).to_be_visible()


def test_PW_LXM_033_announce_interval_input(authenticated_page, base_url):
    """LXMF announce interval input is present."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("general")
    expect(lp.lxmf_announce_interval).to_be_visible()


def test_PW_LXM_034_delivery_transfer_max_size(authenticated_page, base_url):
    """Delivery transfer max size input is present."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("general")
    expect(lp.delivery_transfer_max_size).to_be_visible()


# ===========================================================================
# Propagation tab (PW-LXM-040-050)
# ===========================================================================

def test_PW_LXM_040_enable_node_toggle(authenticated_page, base_url):
    """Toggling enable_node shows/hides dependent fields."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("propagation")
    lp.set_enable_node(True)
    lp.expect_propagation_dep_visible()

    lp.set_enable_node(False)
    lp.expect_propagation_dep_hidden()


def test_PW_LXM_041_propagation_disabled_msg(authenticated_page, base_url):
    """#propagation-disabled-msg visible when enable_node is unchecked."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("propagation")
    lp.set_enable_node(False)
    expect(lp.propagation_disabled_msg).to_be_visible()


def test_PW_LXM_049_050_propagation_dep_visibility(authenticated_page, base_url):
    """Dep fields hidden when off, visible when on."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("propagation")

    lp.set_enable_node(False)
    lp.expect_propagation_dep_hidden()

    lp.set_enable_node(True)
    lp.expect_propagation_dep_visible()


# ===========================================================================
# Sync size validation (PW-LXM-046-048)
# ===========================================================================

def test_PW_LXM_048_sync_size_warning(authenticated_page, base_url):
    """Sync size warning appears when max_sync < 40 * max_msg.

    Set max_msg=1000, max_sync=30000 (< 40*1000=40000) -> warning visible.
    Set max_sync=50000 -> warning hidden.
    """
    lp = _lxmf_page(authenticated_page, base_url)

    _enable_propagation(lp)
    lp.fill_sync_sizes("1000", "30000")
    # Trigger validation by blurring
    lp.propagation_sync_max_size.blur()
    lp.expect_sync_size_warn_visible()

    lp.fill_sync_sizes("1000", "50000")
    lp.propagation_sync_max_size.blur()
    lp.expect_sync_size_warn_hidden()


# ===========================================================================
# Stamp Costs tab (PW-LXM-060-062)
# ===========================================================================

def test_PW_LXM_060_061_stamp_cost_fields(authenticated_page, base_url):
    """Stamp cost target and flexibility fields are present and fillable."""
    lp = _lxmf_page(authenticated_page, base_url)

    _enable_propagation(lp)
    lp.select_tab("costs")
    expect(lp.stamp_cost_target).to_be_visible()
    expect(lp.stamp_cost_flexibility).to_be_visible()

    lp.fill_stamp_costs("14", "2")
    expect(lp.stamp_cost_target).to_have_value("14")
    expect(lp.stamp_cost_flexibility).to_have_value("2")


def test_PW_LXM_062_stamp_floor_warning(authenticated_page, base_url):
    """Stamp floor warning when target - flexibility < 13.

    target=14, flexibility=2 -> floor=12 < 13 -> warning visible.
    target=15, flexibility=2 -> floor=13 -> warning hidden.
    """
    lp = _lxmf_page(authenticated_page, base_url)

    _enable_propagation(lp)
    lp.select_tab("costs")

    lp.fill_stamp_costs("14", "2")
    lp.stamp_cost_flexibility.blur()
    lp.expect_stamp_floor_warn_visible()

    lp.fill_stamp_costs("15", "2")
    lp.stamp_cost_flexibility.blur()
    lp.expect_stamp_floor_warn_hidden()


# ===========================================================================
# Peering tab (PW-LXM-070-075)
# ===========================================================================

def test_PW_LXM_070_071_autopeer_fields(authenticated_page, base_url):
    """Autopeer checkbox and maxdepth field are present."""
    lp = _lxmf_page(authenticated_page, base_url)

    _enable_propagation(lp)
    lp.select_tab("peering")
    expect(lp.autopeer).to_be_visible()
    expect(lp.autopeer_maxdepth).to_be_visible()


def test_PW_LXM_073_from_static_only_checkbox(authenticated_page, base_url):
    """From static only checkbox is present and toggleable."""
    lp = _lxmf_page(authenticated_page, base_url)

    _enable_propagation(lp)
    lp.select_tab("peering")
    expect(lp.from_static_only).to_be_visible()
    expect(lp.from_static_only).to_be_enabled()


def test_PW_LXM_074_static_peers_tokenizer(authenticated_page, base_url):
    """Can add a hex hash token to the static_peers tokenizer."""
    lp = _lxmf_page(authenticated_page, base_url)

    _enable_propagation(lp)
    lp.select_tab("peering")
    test_hash = "a" * 64
    lp.add_static_peer(test_hash)

    # Verify the token was added by checking either the select2 choice
    # elements or the hidden input's value.
    authenticated_page.wait_for_timeout(500)
    parent = authenticated_page.locator("#lxmf\\.static_peers").locator("xpath=..")
    token = parent.locator(".select2-search-choice, .token")
    if token.count() > 0:
        expect(token.first).to_contain_text(test_hash[:8], timeout=5_000)
    else:
        # Fallback: check the hidden input's value
        val = authenticated_page.locator("#lxmf\\.static_peers").input_value()
        assert test_hash[:8] in val, (
            f"Token not found in input value: {val!r}"
        )


def test_PW_LXM_075_static_only_warning(authenticated_page, base_url):
    """Check from_static_only with empty static_peers -> warning visible.

    Adding a peer should hide the warning.
    """
    lp = _lxmf_page(authenticated_page, base_url)

    _enable_propagation(lp)
    lp.select_tab("peering")

    # Clear any existing peers and check from_static_only
    lp.set_from_static_only(True)
    lp.expect_static_only_warn_visible()

    # Add a peer to dismiss the warning
    lp.add_static_peer("b" * 64)
    lp.expect_static_only_warn_hidden()


# ===========================================================================
# ACL tab (PW-LXM-080-084)
# ===========================================================================

def test_PW_LXM_080_084_acl_fields_present(authenticated_page, base_url):
    """All ACL fields are present on the ACL tab."""
    lp = _lxmf_page(authenticated_page, base_url)

    _enable_propagation(lp)
    lp.select_tab("acl")

    expect(lp.auth_required).to_be_visible()
    expect(lp.control_allowed).to_be_visible()
    expect(lp.allowed_identities).to_be_visible()
    expect(lp.ignored_destinations).to_be_visible()
    expect(lp.prioritise_destinations).to_be_visible()


# ===========================================================================
# Logging tab (PW-LXM-090-093)
# ===========================================================================

def test_PW_LXM_090_091_logging_fields(authenticated_page, base_url):
    """Loglevel select and logfile input are present."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("logging")
    expect(lp.loglevel).to_be_visible()
    expect(lp.logfile).to_be_visible()


def test_PW_LXM_093_on_inbound_warning(authenticated_page, base_url):
    """Typing a value in on_inbound shows the security warning."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.select_tab("logging")
    lp.on_inbound.fill("/usr/local/bin/handler.sh")
    lp.on_inbound.blur()
    expect(lp.on_inbound_warn).to_be_visible()


# ===========================================================================
# Form footer (PW-LXM-095-097)
# ===========================================================================

def test_PW_LXM_095_save_button(authenticated_page, base_url):
    """Save button is present and clickable."""
    lp = _lxmf_page(authenticated_page, base_url)

    expect(lp.save_btn).to_be_visible()
    expect(lp.save_btn).to_be_enabled()


def test_PW_LXM_096_097_apply_changes(
    authenticated_page, base_url, save_and_restore_general
):
    """Apply button works and success message appears."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.save()
    lp.apply_changes()
    expect(lp.apply_success_msg).to_be_visible()


# ===========================================================================
# Tests requiring stopped rnsd — MUST be at END of file
# ===========================================================================

@pytest.mark.requires_stopped_rnsd
def test_PW_LXM_008_start_disabled_when_rnsd_stopped(
    authenticated_page, base_url, ensure_rnsd_stopped
):
    """With rnsd stopped, Start and Restart buttons are disabled."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.expect_lxmd_start_disabled()
    expect(lp.lxmd_btn_restart).to_be_disabled()


@pytest.mark.requires_stopped_rnsd
def test_PW_LXM_009_010_rnsd_warning_when_stopped(
    authenticated_page, base_url, ensure_rnsd_stopped
):
    """With rnsd stopped, #rnsd-warning is visible."""
    lp = _lxmf_page(authenticated_page, base_url)

    lp.expect_rnsd_warning_visible()
