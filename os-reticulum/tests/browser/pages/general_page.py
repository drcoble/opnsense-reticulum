"""Page object for the Reticulum General Settings page.

URL: /ui/reticulum/general
"""

import re

from playwright.sync_api import Page, Locator, expect

from .base_page import BasePage


class GeneralPage(BasePage):
    """Interactions and assertions for /ui/reticulum/general."""

    PATH = "/ui/reticulum/general"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    # -- Navigation ----------------------------------------------------------

    def navigate(self) -> None:
        """Open the general settings page and wait for tab strip."""
        self.goto(self.PATH)
        self.page.wait_for_selector(
            "#maintabs", state="visible", timeout=self.PAGE_READY_TIMEOUT
        )

    # -- Tab helpers ---------------------------------------------------------

    _TAB_MAP = {
        "general": "#tab-general",
        "transport": "#tab-transport",
        "sharing": "#tab-sharing",
        "management": "#tab-management",
        "logging": "#tab-logging",
    }

    def select_tab(self, tab_name: str) -> None:
        """Click a tab by logical name and wait for its pane to become active."""
        href = self._TAB_MAP[tab_name]
        self.page.locator(f'#maintabs a[href="{href}"]').click()
        self.page.locator(f"{href}.active, {href}.in").wait_for(state="visible")

    # -- Runtime info --------------------------------------------------------

    @property
    def rnsd_version(self) -> Locator:
        return self.page.locator("#rnsd-version")

    @property
    def rnsd_identity(self) -> Locator:
        return self.page.locator("#rnsd-identity")

    @property
    def rnsd_uptime(self) -> Locator:
        return self.page.locator("#rnsd-uptime")

    def get_runtime_info(self) -> dict:
        """Return a dict with version, identity, and uptime text."""
        return {
            "version": self.rnsd_version.inner_text(),
            "identity": self.rnsd_identity.inner_text(),
            "uptime": self.rnsd_uptime.inner_text(),
        }

    # -- General tab ---------------------------------------------------------

    @property
    def enabled_checkbox(self) -> Locator:
        return self.page.locator("#general\\.enabled")

    def set_enabled(self, value: bool) -> None:
        """Check or uncheck the service-enabled checkbox."""
        if self.enabled_checkbox.is_checked() != value:
            self.enabled_checkbox.click()

    # -- Transport tab -------------------------------------------------------

    @property
    def enable_transport_checkbox(self) -> Locator:
        return self.page.locator("#general\\.enable_transport")

    @property
    def respond_to_probes_checkbox(self) -> Locator:
        return self.page.locator("#general\\.respond_to_probes")

    @property
    def panic_on_interface_error_checkbox(self) -> Locator:
        return self.page.locator("#general\\.panic_on_interface_error")

    def set_enable_transport(self, value: bool) -> None:
        if self.enable_transport_checkbox.is_checked() != value:
            self.enable_transport_checkbox.click()

    # -- Sharing tab ---------------------------------------------------------

    @property
    def share_instance_checkbox(self) -> Locator:
        return self.page.locator("#general\\.share_instance")

    @property
    def shared_instance_port(self) -> Locator:
        return self.page.locator("#general\\.shared_instance_port")

    @property
    def instance_control_port(self) -> Locator:
        return self.page.locator("#general\\.instance_control_port")

    @property
    def port_conflict_msg(self) -> Locator:
        return self.page.locator("#port-conflict-msg")

    @property
    def sharing_disabled_msg(self) -> Locator:
        return self.page.locator("#sharing-disabled-msg")

    @property
    def share_instance_dep(self) -> Locator:
        return self.page.locator(".share_instance_dep")

    def set_share_instance(self, value: bool) -> None:
        """Toggle share_instance and wait for dep field visibility change."""
        if self.share_instance_checkbox.is_checked() != value:
            self.share_instance_checkbox.click()
            if value:
                self.share_instance_dep.first.wait_for(state="visible")
            else:
                self.share_instance_dep.first.wait_for(state="hidden")

    def fill_sharing_ports(self, app_port: str, mgmt_port: str) -> None:
        """Fill both sharing port fields."""
        self.shared_instance_port.fill(app_port)
        self.instance_control_port.fill(mgmt_port)

    # -- Management tab ------------------------------------------------------

    @property
    def enable_remote_management_checkbox(self) -> Locator:
        return self.page.locator("#general\\.enable_remote_management")

    @property
    def remote_mgmt_dep_fields(self) -> Locator:
        return self.page.locator("#remote-mgmt-dep-fields")

    @property
    def remote_management_allowed(self) -> Locator:
        return self.page.locator("#general\\.remote_management_allowed")

    @property
    def rpc_key(self) -> Locator:
        return self.page.locator("#general\\.rpc_key")

    @property
    def remote_mgmt_disabled_msg(self) -> Locator:
        return self.page.locator("#remote-mgmt-disabled-msg")

    def set_remote_management(self, value: bool) -> None:
        """Toggle remote management and wait for dep fields."""
        if self.enable_remote_management_checkbox.is_checked() != value:
            self.enable_remote_management_checkbox.click()
            if value:
                self.remote_mgmt_dep_fields.wait_for(state="visible")
            else:
                self.remote_mgmt_dep_fields.wait_for(state="hidden")

    def add_remote_admin(self, hex_hash: str) -> None:
        """Type a hex identity hash into the tokenizer and press Enter.

        OPNsense's formatTokenizersUI() transforms the original <input>
        into a select2 (v3) tokenizer.  The visible search input is an
        ``<input class="select2-input">`` inside a ``<ul class="select2-choices">``
        container.  We locate it relative to the original element's parent
        ``<div>`` which contains both the hidden original and the select2 widget.
        """
        # The select2 container is a sibling of the original input.
        # Click the select2 choices area to focus the search input.
        parent = self.remote_management_allowed.locator("xpath=..")
        search_input = parent.locator("input.select2-input")
        if search_input.count() > 0:
            search_input.click()
            search_input.fill(hex_hash)
            search_input.press("Enter")
        else:
            # Fallback: no select2 transformation, use the raw input
            self.remote_management_allowed.fill(hex_hash)
            self.remote_management_allowed.press("Enter")

    # -- Logging tab ---------------------------------------------------------

    @property
    def loglevel_select(self) -> Locator:
        return self.page.locator("#general\\.loglevel")

    @property
    def logfile_input(self) -> Locator:
        return self.page.locator("#general\\.logfile")

    def set_loglevel(self, value: str) -> None:
        """Select log level by option value (0-7)."""
        self.loglevel_select.select_option(value=value)

    # -- Form actions --------------------------------------------------------

    @property
    def save_btn(self) -> Locator:
        return self.page.locator("#saveBtn")

    @property
    def apply_btn(self) -> Locator:
        return self.page.locator("#applyBtn")

    @property
    def apply_success_msg(self) -> Locator:
        return self.page.locator("#apply-success-msg")

    def save(self) -> None:
        """Click Save and wait for the AJAX response to complete."""
        self.save_btn.click()
        self.wait_for_spinner_gone()

    def apply_changes(self) -> None:
        """Click Apply Changes and wait for the success message."""
        self.apply_btn.click()
        self.apply_success_msg.wait_for(state="visible")

    # -- Service bar ---------------------------------------------------------

    @property
    def service_status_container(self) -> Locator:
        return self.page.locator("#service_status_container")

    def get_service_status(self) -> str:
        """Return the service state based on indicator icons.

        OPNsense's updateServiceControlUI() renders:
          - Running: ``<span class="label label-success">`` (green)
          - Stopped: ``<span class="label label-danger">`` (red)
        Falls back to inner text if neither label class is found.
        """
        if self.service_status_container.locator(".label-success").count() > 0:
            return "running"
        if self.service_status_container.locator(".label-danger").count() > 0:
            return "stopped"
        return self.service_status_container.inner_text().strip()

    def _wait_for_service_action(self) -> None:
        """Wait for the OPNsense standard wait dialog to appear then close.

        ``updateServiceControlUI`` shows ``#OPNsenseStdWaitDialog`` while the
        start/stop/restart API call is in flight.  After the call completes it
        hides the dialog and re-fetches status.  We wait for the dialog to
        become visible (proving the click registered), then wait for it to
        disappear (proving the action completed).
        """
        wait_dialog = self.page.locator("#OPNsenseStdWaitDialog")
        try:
            wait_dialog.wait_for(state="visible", timeout=5_000)
        except Exception:
            pass  # Dialog may flash too fast to catch
        wait_dialog.wait_for(state="hidden", timeout=30_000)
        # Allow the follow-up status refresh to complete
        self.page.wait_for_timeout(2000)

    def click_start(self) -> None:
        """Click the Start button injected by updateServiceControlUI().

        The core JS creates ``<span id="startService" class="btn btn-sm">``
        inside ``#service_status_container``.
        """
        # Wait for the start button to appear (only rendered when stopped)
        self.page.locator("#startService").wait_for(state="visible", timeout=15_000)
        self.page.locator("#startService").click()
        self._wait_for_service_action()

    def click_stop(self) -> None:
        """Click the Stop button injected by updateServiceControlUI()."""
        self.page.locator("#stopService").wait_for(state="visible", timeout=15_000)
        self.page.locator("#stopService").click()
        self._wait_for_service_action()

    def click_restart(self) -> None:
        """Click the Restart button injected by updateServiceControlUI()."""
        self.page.locator("#restartService").wait_for(state="visible", timeout=15_000)
        self.page.locator("#restartService").click()
        self._wait_for_service_action()

    # -- Assertion helpers ---------------------------------------------------

    def expect_tab_active(self, tab_name: str) -> None:
        href = self._TAB_MAP[tab_name]
        expect(self.page.locator(f"{href}")).to_have_class(
            expected=re.compile(r".*active.*")
        )

    def expect_share_dep_visible(self) -> None:
        expect(self.share_instance_dep.first).to_be_visible()

    def expect_share_dep_hidden(self) -> None:
        expect(self.share_instance_dep.first).to_be_hidden()

    def expect_port_conflict_visible(self) -> None:
        expect(self.port_conflict_msg).to_be_visible()

    def expect_port_conflict_hidden(self) -> None:
        expect(self.port_conflict_msg).to_be_hidden()

    def expect_remote_mgmt_fields_visible(self) -> None:
        expect(self.remote_mgmt_dep_fields).to_be_visible()

    def expect_remote_mgmt_fields_hidden(self) -> None:
        expect(self.remote_mgmt_dep_fields).to_be_hidden()

    def expect_apply_success_visible(self) -> None:
        expect(self.apply_success_msg).to_be_visible()

    def expect_version_loaded(self) -> None:
        """Assert that the runtime version field no longer says 'loading...'.

        The AJAX call to rnsdInfo may take a few seconds to return after
        page load, so allow a generous timeout.
        """
        expect(self.rnsd_version).not_to_have_text("loading...", timeout=15_000)

    def expect_service_running(self) -> None:
        """Assert the service bar indicates a running state.

        OPNsense's updateServiceControlUI() renders a label with class
        ``label-success`` when the service reports ``"running"``.
        """
        running_indicator = self.service_status_container.locator(
            ".label-success"
        )
        expect(running_indicator.first).to_be_visible(timeout=15_000)

    def expect_service_stopped(self) -> None:
        """Assert the service bar indicates a stopped state.

        OPNsense's updateServiceControlUI() renders a label with class
        ``label-danger`` when the service reports ``"stopped"``.
        """
        stopped_indicator = self.service_status_container.locator(
            ".label-danger"
        )
        expect(stopped_indicator.first).to_be_visible(timeout=15_000)
