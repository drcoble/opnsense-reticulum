"""Page object for the Reticulum Interfaces page.

URL: /ui/reticulum/interfaces
"""

from playwright.sync_api import Page, Locator, expect

from .base_page import BasePage


class InterfacesPage(BasePage):
    """Interactions and assertions for /ui/reticulum/interfaces."""

    PATH = "/ui/reticulum/interfaces"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    # -- Navigation ----------------------------------------------------------

    def navigate(self) -> None:
        """Open the interfaces page and wait for the grid to be ready."""
        self.goto(self.PATH)
        self.page.wait_for_selector(
            "#grid-interfaces", state="visible", timeout=self.PAGE_READY_TIMEOUT
        )
        # Wait for bootgrid JS to initialise — it adds a footer element
        # once initialisation completes (even on an empty data set).
        self.page.wait_for_selector(
            "#grid-interfaces .bootgrid-footer, #grid-interfaces tbody",
            state="attached",
            timeout=self.PAGE_READY_TIMEOUT,
        )
        # Small extra wait for AJAX data fetch to complete
        self.page.wait_for_timeout(1000)

    # -- Grid locators -------------------------------------------------------

    @property
    def grid(self) -> Locator:
        return self.page.locator("#grid-interfaces")

    @property
    def add_btn(self) -> Locator:
        return self.page.locator("#addInterfaceBtn")

    @property
    def apply_btn(self) -> Locator:
        return self.page.locator("#applyInterfacesBtn")

    @property
    def apply_success_msg(self) -> Locator:
        return self.page.locator("#apply-success-msg")

    # -- Grid methods --------------------------------------------------------

    def grid_row_count(self) -> int:
        """Return the number of data rows in the bootgrid table body.

        Excludes the special "no results" row that bootgrid renders when
        the data set is empty, and the loading row.
        """
        return self.grid.locator(
            "tbody tr:not(.no-results):not(.loading)"
        ).count()

    def get_row_by_name(self, name: str) -> Locator:
        """Return the table row whose name column matches *name*.

        Waits briefly for the grid to contain data after a reload/navigation.
        """
        row = self.grid.locator(f"tbody tr:has(td:text-is('{name}'))")
        # Give bootgrid time to populate after AJAX reload
        try:
            row.first.wait_for(state="attached", timeout=5_000)
        except Exception:
            pass  # Caller will check .count()
        return row

    def click_add(self) -> None:
        """Click the Add Interface button and wait for the modal to appear.

        Also waits for the modal's ``shown.bs.modal`` event to complete
        (which triggers type visibility setup and name conflict fetch).
        """
        self.add_btn.click()
        self.page.locator("#DialogInterface").wait_for(state="visible")
        # Wait for the modal transition animation to complete
        self.page.wait_for_timeout(500)

    def click_edit(self, name: str) -> None:
        """Click the edit button on the row matching *name*.

        UIBootgrid handles fetching data and populating the form.
        We wait for the modal to be fully visible and for the form
        to populate (shown.bs.modal fires updateTypeVisibility).
        """
        row = self.get_row_by_name(name)
        row.locator("button.command-edit").click()
        self.page.locator("#DialogInterface").wait_for(state="visible")
        # Wait for AJAX form population and shown.bs.modal handlers
        self.page.wait_for_timeout(1000)

    def click_delete(self, name: str) -> None:
        """Click the delete button on the row matching *name*."""
        row = self.get_row_by_name(name)
        row.locator("a.command-delete, button.command-delete").click()

    def confirm_delete(self) -> None:
        """Click confirm in the custom delete confirmation dialog."""
        delete_modal = self.page.locator("#DialogDeleteInterface")
        delete_modal.wait_for(state="visible", timeout=5_000)
        delete_modal.locator("#btn-confirm-delete").click()
        delete_modal.wait_for(state="hidden", timeout=10_000)

    def cancel_delete(self) -> None:
        """Click cancel in the custom delete confirmation dialog."""
        delete_modal = self.page.locator("#DialogDeleteInterface")
        delete_modal.wait_for(state="visible", timeout=5_000)
        delete_modal.locator("[data-dismiss='modal']").first.click()
        delete_modal.wait_for(state="hidden", timeout=5_000)

    def click_apply(self) -> None:
        """Click Apply Changes."""
        self.apply_btn.click()
        self.apply_success_msg.wait_for(state="visible")

    def toggle_enabled(self, name: str) -> None:
        """Click the inline enabled toggle for the named interface.

        UIBootgrid's ``rowtoggle`` formatter renders a ``<span>`` with
        class ``fa-play`` (enabled) or ``fa-ban`` (disabled) inside a
        ``command-toggle`` wrapper.
        """
        row = self.get_row_by_name(name)
        toggle = row.locator(".command-toggle, .fa-play, .fa-ban, input[type='checkbox']")
        toggle.first.click()
        self.page.wait_for_timeout(1000)

    # -- Modal locators ------------------------------------------------------

    @property
    def modal(self) -> Locator:
        return self.page.locator("#DialogInterface")

    def modal_visible(self) -> bool:
        return self.modal.is_visible()

    # -- Modal tab helpers ---------------------------------------------------

    _MODAL_TAB_MAP = {
        "basic": "#tab-interface-basic",
        "network": "#tab-interface-network",
        "radio": "#tab-interface-radio",
        "advanced": "#tab-interface-advanced",
    }

    def select_modal_tab(self, tab_name: str) -> None:
        """Click a modal tab by logical name."""
        href = self._MODAL_TAB_MAP[tab_name]
        self.modal.locator(f'a[href="{href}"]').click()
        self.page.locator(f"{href}.active, {href}.in").wait_for(state="visible")

    # -- Basic tab fields ----------------------------------------------------

    @property
    def interface_enabled(self) -> Locator:
        return self.page.locator("#interface\\.enabled")

    @property
    def interface_name(self) -> Locator:
        return self.page.locator("#interface\\.name")

    @property
    def interface_type(self) -> Locator:
        return self.page.locator("#interface\\.type")

    @property
    def interface_mode(self) -> Locator:
        return self.page.locator("#interface\\.mode")

    @property
    def interface_outgoing(self) -> Locator:
        return self.page.locator("#interface\\.outgoing")

    @property
    def interface_bootstrap_only(self) -> Locator:
        return self.page.locator("#interface\\.bootstrap_only")

    @property
    def interface_network_name(self) -> Locator:
        return self.page.locator("#interface\\.network_name")

    @property
    def interface_passphrase(self) -> Locator:
        return self.page.locator("#interface\\.passphrase")

    @property
    def interface_ifac_size(self) -> Locator:
        return self.page.locator("#interface\\.ifac_size")

    @property
    def name_conflict_msg(self) -> Locator:
        return self.page.locator("#interface-name-conflict")

    # -- Network tab fields --------------------------------------------------

    @property
    def listen_ip(self) -> Locator:
        return self.page.locator("#interface\\.listen_ip")

    @property
    def listen_port(self) -> Locator:
        return self.page.locator("#interface\\.listen_port")

    @property
    def target_host(self) -> Locator:
        return self.page.locator("#interface\\.target_host")

    @property
    def target_port(self) -> Locator:
        return self.page.locator("#interface\\.target_port")

    @property
    def prefer_ipv6(self) -> Locator:
        return self.page.locator("#interface\\.prefer_ipv6")

    @property
    def net_interface(self) -> Locator:
        """The 'interface' field (bind device for TCP)."""
        return self.page.locator("#interface\\.interface")

    @property
    def i2p_tunneled(self) -> Locator:
        return self.page.locator("#interface\\.i2p_tunneled")

    @property
    def kiss_framing(self) -> Locator:
        return self.page.locator("#interface\\.kiss_framing")

    @property
    def mtu(self) -> Locator:
        return self.page.locator("#interface\\.mtu")

    @property
    def forward_ip(self) -> Locator:
        return self.page.locator("#interface\\.forward_ip")

    @property
    def forward_port(self) -> Locator:
        return self.page.locator("#interface\\.forward_port")

    @property
    def group_id(self) -> Locator:
        return self.page.locator("#interface\\.group_id")

    @property
    def discovery_scope(self) -> Locator:
        return self.page.locator("#interface\\.discovery_scope")

    @property
    def discovery_port(self) -> Locator:
        return self.page.locator("#interface\\.discovery_port")

    @property
    def data_port(self) -> Locator:
        return self.page.locator("#interface\\.data_port")

    @property
    def devices(self) -> Locator:
        return self.page.locator("#interface\\.devices")

    @property
    def ignored_devices(self) -> Locator:
        return self.page.locator("#interface\\.ignored_devices")

    # -- Radio / Serial tab fields -------------------------------------------

    @property
    def port(self) -> Locator:
        return self.page.locator("#interface\\.port")

    @property
    def frequency(self) -> Locator:
        return self.page.locator("#interface\\.frequency")

    @property
    def bandwidth(self) -> Locator:
        return self.page.locator("#interface\\.bandwidth")

    @property
    def txpower(self) -> Locator:
        return self.page.locator("#interface\\.txpower")

    @property
    def spreading_factor(self) -> Locator:
        return self.page.locator("#interface\\.spreadingfactor")

    @property
    def coding_rate(self) -> Locator:
        return self.page.locator("#interface\\.codingrate")

    @property
    def airtime_limit_long(self) -> Locator:
        return self.page.locator("#interface\\.airtime_limit_long")

    @property
    def airtime_limit_short(self) -> Locator:
        return self.page.locator("#interface\\.airtime_limit_short")

    @property
    def speed(self) -> Locator:
        return self.page.locator("#interface\\.speed")

    @property
    def databits(self) -> Locator:
        return self.page.locator("#interface\\.databits")

    @property
    def parity(self) -> Locator:
        return self.page.locator("#interface\\.parity")

    @property
    def stopbits(self) -> Locator:
        return self.page.locator("#interface\\.stopbits")

    @property
    def preamble(self) -> Locator:
        return self.page.locator("#interface\\.preamble")

    @property
    def txtail(self) -> Locator:
        return self.page.locator("#interface\\.txtail")

    @property
    def persistence(self) -> Locator:
        return self.page.locator("#interface\\.persistence")

    @property
    def slottime(self) -> Locator:
        return self.page.locator("#interface\\.slottime")

    @property
    def callsign(self) -> Locator:
        return self.page.locator("#interface\\.callsign")

    @property
    def ssid(self) -> Locator:
        return self.page.locator("#interface\\.ssid")

    @property
    def command(self) -> Locator:
        return self.page.locator("#interface\\.command")

    @property
    def respawn_delay(self) -> Locator:
        return self.page.locator("#interface\\.respawn_delay")

    @property
    def rnode_multi_config(self) -> Locator:
        return self.page.locator("#interface\\.sub_interfaces_raw")

    @property
    def flow_control(self) -> Locator:
        return self.page.locator("#interface\\.flow_control")

    @property
    def id_callsign(self) -> Locator:
        return self.page.locator("#interface\\.id_callsign")

    @property
    def id_interval(self) -> Locator:
        return self.page.locator("#interface\\.id_interval")

    # -- Modal action methods ------------------------------------------------

    def set_name(self, name: str) -> None:
        self.interface_name.fill(name)

    def set_type(self, type_value: str) -> None:
        """Select interface type by option value (e.g. 'TCPServerInterface').

        After selecting, explicitly triggers a jQuery ``change`` event
        so the ``updateTypeVisibility()`` handler fires (Playwright's
        native change event may not propagate to jQuery's delegated handler).
        """
        self.interface_type.select_option(value=type_value)
        self.page.evaluate(
            "document.querySelector('#interface\\\\.type').dispatchEvent("
            "new Event('change', {bubbles: true}))"
        )

    def set_mode(self, mode: str) -> None:
        self.interface_mode.select_option(value=mode)

    def set_enabled_modal(self, value: bool) -> None:
        if self.interface_enabled.is_checked() != value:
            self.interface_enabled.click()

    def set_listen_port(self, port: str) -> None:
        self.listen_port.fill(port)

    def set_listen_ip(self, ip: str) -> None:
        self.listen_ip.fill(ip)

    def set_target_host(self, host: str) -> None:
        self.target_host.fill(host)

    def set_target_port(self, port: str) -> None:
        self.target_port.fill(port)

    def set_frequency(self, freq: str) -> None:
        self.frequency.fill(freq)

    def set_bandwidth(self, bw: str) -> None:
        self.bandwidth.fill(bw)

    def set_txpower(self, pwr: str) -> None:
        self.txpower.fill(pwr)

    def set_spreading_factor(self, sf: str) -> None:
        self.spreading_factor.fill(sf)

    def set_coding_rate(self, cr: str) -> None:
        self.coding_rate.fill(cr)

    def set_serial_port(self, port: str) -> None:
        self.port.fill(port)

    def set_speed(self, speed: str) -> None:
        self.speed.fill(speed)

    def set_pipe_command(self, cmd: str) -> None:
        self.command.fill(cmd)

    def save_modal(self) -> None:
        """Click the modal save button and wait for the modal to close."""
        self.page.locator("#btn-save-interface").click()
        self.modal.wait_for(state="hidden", timeout=10_000)

    def cancel_modal(self) -> None:
        """Click cancel or the close button on the modal."""
        self.modal.locator("[data-dismiss='modal'], button:has-text('Cancel')").first.click()
        self.modal.wait_for(state="hidden")

    def fields_visible_for_type(self, type_value: str) -> set:
        """Return the set of type-conditional CSS classes currently shown.

        The interface form uses classes like ``.type-tcp``, ``.type-udp``,
        ``.type-auto``, etc. to show/hide groups of fields based on the
        selected interface type.  jQuery ``.show()``/``.hide()`` toggle
        ``display: none`` on these elements.

        We check the element's own ``display`` style rather than using
        Playwright's ``is_visible()`` because fields on inactive tab
        panes are not "visible" in the DOM sense even when their own
        ``display`` is not ``none``.
        """
        visible = set()
        type_classes = [
            "type-tcp", "type-tcp-server", "type-udp", "type-auto",
            "type-rnode", "type-serial", "type-kiss", "type-ax25",
            "type-pipe", "type-i2p", "type-multi", "type-discover",
        ]
        for cls in type_classes:
            locator = self.modal.locator(f".{cls}").first
            if locator.count() > 0:
                # Check the element's own inline display style.
                # jQuery .hide() sets el.style.display = 'none';
                # jQuery .show() clears it (el.style.display = '').
                # We only care whether the type-visibility JS has hidden
                # the element, not whether its parent tab pane is active.
                is_shown = locator.evaluate(
                    "el => el.style.display !== 'none'"
                )
                if is_shown:
                    visible.add(cls)
        return visible

    # -- Assertion helpers ---------------------------------------------------

    def expect_name_conflict_visible(self) -> None:
        expect(self.name_conflict_msg).to_be_visible()

    def expect_name_conflict_hidden(self) -> None:
        expect(self.name_conflict_msg).to_be_hidden()
