"""Page object for the Reticulum LXMF Propagation Node page.

URL: /ui/reticulum/lxmf
"""

from playwright.sync_api import Page, Locator, expect

from .base_page import BasePage


class LxmfPage(BasePage):
    """Interactions and assertions for /ui/reticulum/lxmf."""

    PATH = "/ui/reticulum/lxmf"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    # -- Navigation ----------------------------------------------------------

    def navigate(self) -> None:
        """Open the LXMF page and wait for the tab strip."""
        self.goto(self.PATH)
        self.page.wait_for_selector(
            "#maintabs", state="visible", timeout=self.PAGE_READY_TIMEOUT
        )

    # -- Tab helpers ---------------------------------------------------------

    _TAB_MAP = {
        "general": "#tab-general",
        "propagation": "#tab-propagation",
        "costs": "#tab-costs",
        "peering": "#tab-peering",
        "acl": "#tab-acl",
        "logging": "#tab-logging",
    }

    def select_tab(self, tab_name: str) -> None:
        """Click a tab by logical name and wait for the pane."""
        href = self._TAB_MAP[tab_name]
        self.page.locator(f'#maintabs a[href="{href}"]').click()
        self.page.locator(f"{href}.active, {href}.in").wait_for(state="visible")

    # -- Dual service bar ----------------------------------------------------

    @property
    def rnsd_status_badge(self) -> Locator:
        return self.page.locator("#rnsd-status-badge")

    @property
    def lxmd_status_badge(self) -> Locator:
        return self.page.locator("#lxmd-status-badge")

    @property
    def lxmd_btn_start(self) -> Locator:
        return self.page.locator("#lxmd-btn-start")

    @property
    def lxmd_btn_stop(self) -> Locator:
        return self.page.locator("#lxmd-btn-stop")

    @property
    def lxmd_btn_restart(self) -> Locator:
        return self.page.locator("#lxmd-btn-restart")

    @property
    def lxmd_action_msg(self) -> Locator:
        return self.page.locator("#lxmd-action-msg")

    @property
    def rnsd_warning(self) -> Locator:
        return self.page.locator("#rnsd-warning")

    def get_rnsd_status(self) -> str:
        return self.rnsd_status_badge.inner_text()

    def get_lxmd_status(self) -> str:
        return self.lxmd_status_badge.inner_text()

    def click_lxmd_start(self) -> None:
        self.lxmd_btn_start.click()
        self.wait_for_spinner_gone()

    def click_lxmd_stop(self) -> None:
        self.lxmd_btn_stop.click()
        self.wait_for_spinner_gone()

    def click_lxmd_restart(self) -> None:
        self.lxmd_btn_restart.click()
        self.wait_for_spinner_gone()

    # -- General tab ---------------------------------------------------------

    @property
    def lxmf_enabled(self) -> Locator:
        return self.page.locator("#lxmf\\.enabled")

    @property
    def display_name(self) -> Locator:
        return self.page.locator("#lxmf\\.display_name")

    @property
    def lxmf_announce_at_start(self) -> Locator:
        return self.page.locator("#lxmf\\.lxmf_announce_at_start")

    @property
    def lxmf_announce_interval(self) -> Locator:
        return self.page.locator("#lxmf\\.lxmf_announce_interval")

    @property
    def delivery_transfer_max_size(self) -> Locator:
        return self.page.locator("#lxmf\\.delivery_transfer_max_size")

    def set_lxmf_enabled(self, value: bool) -> None:
        if self.lxmf_enabled.is_checked() != value:
            self.lxmf_enabled.click()

    # -- Propagation tab -----------------------------------------------------

    @property
    def enable_node(self) -> Locator:
        return self.page.locator("#lxmf\\.enable_node")

    @property
    def propagation_disabled_msg(self) -> Locator:
        return self.page.locator("#propagation-disabled-msg")

    @property
    def propagation_dep(self) -> Locator:
        return self.page.locator(".propagation-dep")

    @property
    def propagation_dep_tab(self) -> Locator:
        return self.page.locator(".propagation-dep-tab")

    @property
    def node_name(self) -> Locator:
        return self.page.locator("#lxmf\\.node_name")

    @property
    def announce_interval(self) -> Locator:
        return self.page.locator("#lxmf\\.announce_interval")

    @property
    def announce_at_start(self) -> Locator:
        return self.page.locator("#lxmf\\.announce_at_start")

    @property
    def message_storage_limit(self) -> Locator:
        return self.page.locator("#lxmf\\.message_storage_limit")

    @property
    def propagation_message_max_size(self) -> Locator:
        return self.page.locator("#lxmf\\.propagation_message_max_size")

    @property
    def propagation_sync_max_size(self) -> Locator:
        return self.page.locator("#lxmf\\.propagation_sync_max_size")

    @property
    def sync_size_warn(self) -> Locator:
        return self.page.locator("#sync-size-warn")

    def set_enable_node(self, value: bool) -> None:
        """Toggle propagation node and wait for dep visibility change."""
        if self.enable_node.is_checked() != value:
            self.enable_node.click()
            if value:
                self.propagation_dep.first.wait_for(state="visible")
            else:
                self.propagation_dep.first.wait_for(state="hidden")

    def fill_sync_sizes(self, max_msg: str, max_sync: str) -> None:
        self.propagation_message_max_size.fill(max_msg)
        self.propagation_sync_max_size.fill(max_sync)

    # -- Stamp Costs tab -----------------------------------------------------

    @property
    def stamp_cost_target(self) -> Locator:
        return self.page.locator("#lxmf\\.stamp_cost_target")

    @property
    def stamp_cost_flexibility(self) -> Locator:
        return self.page.locator("#lxmf\\.stamp_cost_flexibility")

    @property
    def stamp_floor_warn(self) -> Locator:
        return self.page.locator("#stamp-floor-warn")

    @property
    def peering_cost(self) -> Locator:
        return self.page.locator("#lxmf\\.peering_cost")

    @property
    def remote_peering_cost_max(self) -> Locator:
        return self.page.locator("#lxmf\\.remote_peering_cost_max")

    def fill_stamp_costs(self, target: str, flexibility: str) -> None:
        self.stamp_cost_target.fill(target)
        self.stamp_cost_flexibility.fill(flexibility)

    # -- Peering tab ---------------------------------------------------------

    @property
    def autopeer(self) -> Locator:
        return self.page.locator("#lxmf\\.autopeer")

    @property
    def autopeer_maxdepth(self) -> Locator:
        return self.page.locator("#lxmf\\.autopeer_maxdepth")

    @property
    def max_peers(self) -> Locator:
        return self.page.locator("#lxmf\\.max_peers")

    @property
    def from_static_only(self) -> Locator:
        return self.page.locator("#lxmf\\.from_static_only")

    @property
    def static_peers(self) -> Locator:
        return self.page.locator("#lxmf\\.static_peers")

    @property
    def static_only_warn(self) -> Locator:
        return self.page.locator("#static-only-warn")

    def set_from_static_only(self, value: bool) -> None:
        if self.from_static_only.is_checked() != value:
            self.from_static_only.click()

    def add_static_peer(self, hex_hash: str) -> None:
        """Type a hex identity hash into the tokenizer and press Enter.

        OPNsense's formatTokenizersUI() transforms the original <input>
        into a select2 widget.  We must interact with the select2 search
        input rather than the hidden original element.
        """
        container = self.static_peers.locator(
            "xpath=following-sibling::*[contains(@class,'select2-container')]"
        )
        if container.count() > 0:
            container.click()
            search_input = self.page.locator(
                ".select2-input:visible, .select2-search__field:visible"
            ).first
            search_input.fill(hex_hash)
            search_input.press("Enter")
        else:
            self.static_peers.fill(hex_hash)
            self.static_peers.press("Enter")

    # -- Access Control tab --------------------------------------------------

    @property
    def auth_required(self) -> Locator:
        return self.page.locator("#lxmf\\.auth_required")

    @property
    def control_allowed(self) -> Locator:
        return self.page.locator("#lxmf\\.control_allowed")

    @property
    def allowed_identities(self) -> Locator:
        return self.page.locator("#lxmf\\.allowed_identities")

    @property
    def ignored_destinations(self) -> Locator:
        return self.page.locator("#lxmf\\.ignored_destinations")

    @property
    def prioritise_destinations(self) -> Locator:
        return self.page.locator("#lxmf\\.prioritise_destinations")

    # -- Logging tab ---------------------------------------------------------

    @property
    def loglevel(self) -> Locator:
        return self.page.locator("#lxmf\\.loglevel")

    @property
    def logfile(self) -> Locator:
        return self.page.locator("#lxmf\\.logfile")

    @property
    def on_inbound(self) -> Locator:
        return self.page.locator("#lxmf\\.on_inbound")

    @property
    def on_inbound_warn(self) -> Locator:
        return self.page.locator("#on-inbound-warn")

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

    # -- Assertion helpers ---------------------------------------------------

    def expect_rnsd_warning_visible(self) -> None:
        expect(self.rnsd_warning).to_be_visible()

    def expect_rnsd_warning_hidden(self) -> None:
        expect(self.rnsd_warning).to_be_hidden()

    def expect_propagation_dep_visible(self) -> None:
        expect(self.propagation_dep.first).to_be_visible()

    def expect_propagation_dep_hidden(self) -> None:
        expect(self.propagation_dep.first).to_be_hidden()

    def expect_propagation_tabs_visible(self) -> None:
        expect(self.propagation_dep_tab.first).to_be_visible()

    def expect_propagation_tabs_hidden(self) -> None:
        expect(self.propagation_dep_tab.first).to_be_hidden()

    def expect_stamp_floor_warn_visible(self) -> None:
        expect(self.stamp_floor_warn).to_be_visible()

    def expect_stamp_floor_warn_hidden(self) -> None:
        expect(self.stamp_floor_warn).to_be_hidden()

    def expect_sync_size_warn_visible(self) -> None:
        expect(self.sync_size_warn).to_be_visible()

    def expect_sync_size_warn_hidden(self) -> None:
        expect(self.sync_size_warn).to_be_hidden()

    def expect_static_only_warn_visible(self) -> None:
        expect(self.static_only_warn).to_be_visible()

    def expect_static_only_warn_hidden(self) -> None:
        expect(self.static_only_warn).to_be_hidden()

    def expect_lxmd_start_disabled(self) -> None:
        expect(self.lxmd_btn_start).to_be_disabled()

    def expect_lxmd_start_enabled(self) -> None:
        expect(self.lxmd_btn_start).to_be_enabled()
