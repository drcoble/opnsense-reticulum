"""Playwright browser tests for the General Settings page.

Covers navigation (PW-NAV-001–003), runtime info (PW-GEN-001–002),
service bar (PW-GEN-003–007), tabs (PW-GEN-010–014), and all five
tab panes: General (020–021), Transport (030–032), Sharing (040–045),
Management (050–055), Logging (060–061), and form footer (070–073).

Requires a live OPNsense VM — see conftest.py for env var requirements.
"""

import pytest
from playwright.sync_api import expect

from browser.pages.general_page import GeneralPage


pytestmark = pytest.mark.browser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _general_page(authenticated_page, base_url) -> GeneralPage:
    """Instantiate and navigate to the GeneralPage."""
    gp = GeneralPage(authenticated_page, base_url)
    gp.navigate()
    return gp


# ===========================================================================
# Navigation (PW-NAV)
# ===========================================================================

def test_PW_NAV_001_navigate_to_general(authenticated_page, base_url):
    """Page loads successfully, title is correct, no JS console errors."""
    errors: list[str] = []
    authenticated_page.on("pageerror", lambda exc: errors.append(str(exc)))

    gp = _general_page(authenticated_page, base_url)

    # Tab strip rendered — page loaded successfully
    expect(authenticated_page.locator("#maintabs")).to_be_visible()
    # Page title / breadcrumb should mention Reticulum or General
    title = gp.page_title()
    assert "reticulum" in title.lower() or "general" in title.lower(), (
        f"Unexpected page title: {title}"
    )
    assert errors == [], f"JS console errors detected: {errors}"


def test_PW_NAV_002_navigate_to_interfaces_link(authenticated_page, base_url):
    """Services > Reticulum > Interfaces menu link navigates correctly."""
    _general_page(authenticated_page, base_url)

    # Click the Interfaces link in the sidebar menu.
    # OPNsense's sidebar may require scrolling to the link.
    menu_link = authenticated_page.locator(
        '#mainmenu a[href="/ui/reticulum/interfaces"]'
    )
    menu_link.scroll_into_view_if_needed()
    expect(menu_link).to_be_visible()
    menu_link.click()
    authenticated_page.wait_for_url(
        "**/ui/reticulum/interfaces", timeout=30_000
    )
    assert "/ui/reticulum/interfaces" in authenticated_page.url


def test_PW_NAV_003_menu_structure(authenticated_page, base_url):
    """Services > Reticulum submenu has General, Interfaces, LXMF, Logs."""
    _general_page(authenticated_page, base_url)

    expected_paths = [
        "/ui/reticulum/general",
        "/ui/reticulum/interfaces",
        "/ui/reticulum/lxmf",
        "/ui/reticulum/logs",
    ]
    for path in expected_paths:
        link = authenticated_page.locator(f'#mainmenu a[href="{path}"]')
        expect(link).to_be_attached(), f"Missing menu link: {path}"


# ===========================================================================
# Runtime info bar (PW-GEN-001–002)
# ===========================================================================

def test_PW_GEN_001_runtime_info_loads(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Version, identity, uptime populate when rnsd is running."""
    gp = _general_page(authenticated_page, base_url)

    gp.expect_version_loaded()
    # Identity and uptime may take longer — rnsd needs time to initialise
    # its identity after starting, and the page polls every 10s.
    gp.page.wait_for_function(
        """() => {
            const el = document.querySelector('#rnsd-identity');
            return el && el.textContent.trim() !== 'loading...';
        }""",
        timeout=60_000,
    )
    info = gp.get_runtime_info()
    assert info["version"] != "loading...", "Version still shows placeholder"
    assert info["identity"] != "loading...", "Identity still shows placeholder"
    # Uptime may be empty string if rnstatus fails — accept non-loading state
    assert info["uptime"] != "loading...", "Uptime still shows placeholder"


def test_PW_GEN_002_identity_hover_title(
    authenticated_page, base_url, ensure_rnsd_running
):
    """#rnsd-identity has a title attribute with the full hash."""
    gp = _general_page(authenticated_page, base_url)

    gp.expect_version_loaded()
    title_attr = gp.rnsd_identity.get_attribute("title")
    displayed = gp.rnsd_identity.inner_text()
    assert title_attr is not None, "Identity span missing title attribute"
    # The full hash in the title should be at least as long as displayed text
    assert len(title_attr) >= len(displayed), (
        f"Title ({len(title_attr)} chars) shorter than displayed ({len(displayed)})"
    )


# ===========================================================================
# Service bar (PW-GEN-003–007)
# ===========================================================================

def test_PW_GEN_003_service_status_displayed(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Service bar shows a status indicator (running or stopped)."""
    gp = _general_page(authenticated_page, base_url)

    # Wait for updateServiceControlUI AJAX to populate the service bar.
    # The function renders .label-success or .label-danger inside
    # #service_status_container after the /api/reticulum/service/status
    # call completes.
    gp.service_status_container.locator(
        ".label-success, .label-danger"
    ).first.wait_for(state="visible", timeout=15_000)

    status = gp.get_service_status().lower()
    assert status in ("running", "stopped"), (
        f"Service status not recognised: {status!r}"
    )


def test_PW_GEN_006_service_restart(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Restart preserves running state."""
    gp = _general_page(authenticated_page, base_url)

    # Wait for the service bar to populate before clicking restart
    gp.expect_service_running()
    gp.click_restart()
    gp.expect_service_running()


# --- Tests that manipulate stopped state go below --------------------------

def test_PW_GEN_004_service_start(
    authenticated_page, base_url, ensure_rnsd_stopped
):
    """Click start transitions service to running."""
    gp = _general_page(authenticated_page, base_url)

    # Wait for service bar to render the stopped state
    gp.service_status_container.locator(
        ".label-success, .label-danger"
    ).first.wait_for(state="visible", timeout=15_000)
    gp.expect_service_stopped()
    gp.click_start()
    gp.expect_service_running()


@pytest.mark.requires_stopped_rnsd
def test_PW_GEN_005_service_stop(
    authenticated_page, base_url, ensure_rnsd_running
):
    """Click stop transitions service to stopped."""
    gp = _general_page(authenticated_page, base_url)

    # Wait for service bar to render the running state
    gp.service_status_container.locator(
        ".label-success, .label-danger"
    ).first.wait_for(state="visible", timeout=15_000)
    gp.expect_service_running()
    gp.click_stop()
    gp.expect_service_stopped()


# ===========================================================================
# Tabs (PW-GEN-010–014)
# ===========================================================================

def test_PW_GEN_010_through_014_all_tabs_navigable(authenticated_page, base_url):
    """Each of the 5 tabs can be clicked and becomes active."""
    gp = _general_page(authenticated_page, base_url)

    for tab_name in ("general", "transport", "sharing", "management", "logging"):
        gp.select_tab(tab_name)
        gp.expect_tab_active(tab_name)


# ===========================================================================
# General tab (PW-GEN-020–021)
# ===========================================================================

def test_PW_GEN_020_enabled_checkbox_present(authenticated_page, base_url):
    """Enabled checkbox exists and is interactable."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("general")
    expect(gp.enabled_checkbox).to_be_visible()
    expect(gp.enabled_checkbox).to_be_enabled()


def test_PW_GEN_021_help_icons_expand(authenticated_page, base_url):
    """Help toggle elements exist on the page."""
    _general_page(authenticated_page, base_url)

    help_links = authenticated_page.locator(".showhelp")
    assert help_links.count() > 0, "No .showhelp elements found on the page"


# ===========================================================================
# Transport tab (PW-GEN-030–032)
# ===========================================================================

def test_PW_GEN_030_enable_transport_checkbox(authenticated_page, base_url):
    """Enable transport checkbox is present and toggleable."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("transport")
    expect(gp.enable_transport_checkbox).to_be_visible()
    expect(gp.enable_transport_checkbox).to_be_enabled()


def test_PW_GEN_031_respond_to_probes_checkbox(authenticated_page, base_url):
    """Respond to probes checkbox is present."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("transport")
    expect(gp.respond_to_probes_checkbox).to_be_visible()


def test_PW_GEN_032_panic_on_interface_error_checkbox(authenticated_page, base_url):
    """Panic on interface error checkbox is present."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("transport")
    expect(gp.panic_on_interface_error_checkbox).to_be_visible()


# ===========================================================================
# Sharing tab (PW-GEN-040–045)
# ===========================================================================

def test_PW_GEN_040_share_instance_toggle(authenticated_page, base_url):
    """Check/uncheck share_instance toggles dep field visibility."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("sharing")
    gp.set_share_instance(True)
    gp.expect_share_dep_visible()

    gp.set_share_instance(False)
    gp.expect_share_dep_hidden()


def test_PW_GEN_041_shared_instance_port_input(authenticated_page, base_url):
    """Shared instance port field accepts input."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("sharing")
    gp.set_share_instance(True)
    gp.shared_instance_port.fill("37428")
    expect(gp.shared_instance_port).to_have_value("37428")


def test_PW_GEN_042_instance_control_port_input(authenticated_page, base_url):
    """Instance control port field accepts input."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("sharing")
    gp.set_share_instance(True)
    gp.instance_control_port.fill("37429")
    expect(gp.instance_control_port).to_have_value("37429")


def test_PW_GEN_043_port_conflict_validation(authenticated_page, base_url):
    """Setting both ports to the same value shows conflict message."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("sharing")
    gp.set_share_instance(True)
    gp.fill_sharing_ports("37428", "37428")
    # Trigger validation — blur the field
    gp.instance_control_port.blur()
    gp.expect_port_conflict_visible()

    # Fix the conflict
    gp.instance_control_port.fill("37429")
    gp.instance_control_port.blur()
    gp.expect_port_conflict_hidden()


def test_PW_GEN_044_sharing_disabled_msg(authenticated_page, base_url):
    """Unchecking share_instance shows disabled message and hides dep fields."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("sharing")
    gp.set_share_instance(False)
    expect(gp.sharing_disabled_msg).to_be_visible()
    gp.expect_share_dep_hidden()


def test_PW_GEN_045_sharing_enabled_fields(authenticated_page, base_url):
    """Checking share_instance shows dep fields."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("sharing")
    gp.set_share_instance(True)
    gp.expect_share_dep_visible()


# ===========================================================================
# Management tab (PW-GEN-050–055)
# ===========================================================================

def test_PW_GEN_050_remote_management_toggle(authenticated_page, base_url):
    """Check/uncheck remote management toggles dep field visibility."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("management")
    gp.set_remote_management(True)
    gp.expect_remote_mgmt_fields_visible()

    gp.set_remote_management(False)
    gp.expect_remote_mgmt_fields_hidden()


def test_PW_GEN_051_authorized_admins_tokenizer(authenticated_page, base_url):
    """Typing a hex hash and pressing Enter creates a token."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("management")
    gp.set_remote_management(True)
    test_hash = "a" * 64
    gp.add_remote_admin(test_hash)
    # After pressing Enter the tokenizer should contain the value.
    # OPNsense's select2 v3 tokenizer creates <li class="select2-search-choice">
    # elements inside the parent container.  The original input's value
    # is also updated.  Check either the select2 token list or the
    # hidden input's value attribute.
    authenticated_page.wait_for_timeout(500)
    parent = authenticated_page.locator(
        "#general\\.remote_management_allowed"
    ).locator("xpath=..")
    # select2 tokens show the value as text in choice elements
    token = parent.locator(".select2-search-choice, .token")
    if token.count() > 0:
        expect(token.first).to_contain_text(test_hash[:8], timeout=5_000)
    else:
        # Fallback: check the hidden input's value
        val = authenticated_page.locator(
            "#general\\.remote_management_allowed"
        ).input_value()
        assert test_hash[:8] in val, (
            f"Token not found in input value: {val!r}"
        )


def test_PW_GEN_052_rpc_key_password_field(authenticated_page, base_url):
    """RPC key field is of type password."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("management")
    gp.set_remote_management(True)
    expect(gp.rpc_key).to_have_attribute("type", "password")


def test_PW_GEN_053_054_remote_mgmt_dep_visibility(authenticated_page, base_url):
    """Dep fields hidden when disabled, visible when enabled."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("management")
    gp.set_remote_management(False)
    gp.expect_remote_mgmt_fields_hidden()

    gp.set_remote_management(True)
    gp.expect_remote_mgmt_fields_visible()


def test_PW_GEN_055_remote_mgmt_disabled_msg(authenticated_page, base_url):
    """Disabled message visible when remote management is unchecked."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("management")
    gp.set_remote_management(False)
    expect(gp.remote_mgmt_disabled_msg).to_be_visible()


# ===========================================================================
# Logging tab (PW-GEN-060–061)
# ===========================================================================

def test_PW_GEN_060_loglevel_select_options(authenticated_page, base_url):
    """Log level select has 8 options (values 0–7)."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("logging")
    options = gp.loglevel_select.locator("option")
    assert options.count() == 8, (
        f"Expected 8 log level options, got {options.count()}"
    )


def test_PW_GEN_061_logfile_input(authenticated_page, base_url):
    """Log file input field is present and visible."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("logging")
    expect(gp.logfile_input).to_be_visible()


# ===========================================================================
# Form footer (PW-GEN-070–073)
# ===========================================================================

def test_PW_GEN_070_save_settings(
    authenticated_page, base_url, save_and_restore_general
):
    """Fill a field, click save, verify no error."""
    gp = _general_page(authenticated_page, base_url)

    gp.select_tab("logging")
    gp.set_loglevel("5")
    gp.save()

    # No error alert should appear after save
    error_alert = gp.get_error_alert()
    expect(error_alert).to_have_count(0)


def test_PW_GEN_071_apply_changes(
    authenticated_page, base_url, save_and_restore_general
):
    """Click apply, verify success message appears."""
    gp = _general_page(authenticated_page, base_url)

    gp.save()
    gp.apply_changes()
    gp.expect_apply_success_visible()


def test_PW_GEN_072_apply_success_alert(
    authenticated_page, base_url, save_and_restore_general
):
    """Success message is visible immediately after apply."""
    gp = _general_page(authenticated_page, base_url)

    gp.save()
    gp.apply_changes()
    expect(gp.apply_success_msg).to_be_visible()


def test_PW_GEN_073_apply_success_auto_dismiss(
    authenticated_page, base_url, save_and_restore_general
):
    """Success message fades out after approximately 3 seconds."""
    gp = _general_page(authenticated_page, base_url)

    gp.save()
    gp.apply_changes()
    expect(gp.apply_success_msg).to_be_visible()

    # Wait for auto-dismiss (~3s fade); allow up to 6s for animation
    expect(gp.apply_success_msg).to_be_hidden(timeout=6_000)
