"""Page object for the OPNsense Dashboard with Reticulum widget.

URL: /ui/dashboard
"""

from playwright.sync_api import Page, Locator, expect

from .base_page import BasePage


class DashboardPage(BasePage):
    """Interactions and assertions for the Reticulum dashboard widget."""

    PATH = "/ui/dashboard"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    # -- Navigation ----------------------------------------------------------

    def navigate(self) -> None:
        """Open the OPNsense dashboard and wait for it to load.

        Waits for the dashboard framework to initialize.  The Reticulum
        widget will only appear if it has been added to the dashboard
        layout by the user (or CI setup).
        """
        self.goto(self.PATH)
        self.page.wait_for_load_state("load")
        # Give the dashboard JS time to render widgets
        self.page.wait_for_timeout(3000)

    # -- Widget container ----------------------------------------------------

    @property
    def widget(self) -> Locator:
        return self.page.locator("#reticulum-widget")

    def widget_visible(self) -> bool:
        return self.widget.is_visible()

    # -- Status rows ---------------------------------------------------------

    @property
    def rnsd_status(self) -> Locator:
        return self.page.locator("#ret-rnsd-status")

    @property
    def lxmd_row(self) -> Locator:
        return self.page.locator("#ret-row-lxmd")

    @property
    def lxmd_status(self) -> Locator:
        return self.page.locator("#ret-lxmd-status")

    def get_rnsd_status(self) -> str:
        return self.rnsd_status.inner_text()

    def get_lxmd_status(self) -> str:
        return self.lxmd_status.inner_text()

    # -- Detail rows ---------------------------------------------------------

    @property
    def ifcount_row(self) -> Locator:
        return self.page.locator("#ret-row-ifcount")

    @property
    def ifcount(self) -> Locator:
        return self.page.locator("#ret-ifcount")

    @property
    def traffic_row(self) -> Locator:
        return self.page.locator("#ret-row-traffic")

    @property
    def traffic(self) -> Locator:
        return self.page.locator("#ret-traffic")

    @property
    def version_row(self) -> Locator:
        return self.page.locator("#ret-row-version")

    @property
    def version(self) -> Locator:
        return self.page.locator("#ret-version")

    @property
    def identity_row(self) -> Locator:
        return self.page.locator("#ret-row-identity")

    @property
    def identity(self) -> Locator:
        return self.page.locator("#ret-identity")

    def get_interface_count(self) -> str:
        return self.ifcount.inner_text()

    def get_traffic(self) -> str:
        return self.traffic.inner_text()

    def get_version(self) -> str:
        return self.version.inner_text()

    def get_identity(self) -> str:
        return self.identity.inner_text()

    # -- Interface table -----------------------------------------------------

    @property
    def iface_table(self) -> Locator:
        return self.page.locator("#ret-iface-table")

    @property
    def iface_list(self) -> Locator:
        return self.page.locator("#ret-iface-list")

    def interface_rows(self) -> list:
        """Return a list of Locators for each row in the interface table body."""
        return self.iface_list.locator("tr").all()

    # -- Degraded state ------------------------------------------------------

    @property
    def degraded(self) -> Locator:
        return self.page.locator("#ret-degraded")

    # -- Compact view --------------------------------------------------------

    @property
    def compact(self) -> Locator:
        return self.page.locator("#ret-compact")

    @property
    def compact_rnsd(self) -> Locator:
        return self.page.locator("#ret-compact-rnsd")

    @property
    def compact_lxmd(self) -> Locator:
        return self.page.locator("#ret-compact-lxmd")

    # -- Assertion helpers ---------------------------------------------------

    def expect_degraded_visible(self) -> None:
        expect(self.degraded).to_be_visible()

    def expect_degraded_hidden(self) -> None:
        expect(self.degraded).to_be_hidden()

    def expect_compact_visible(self) -> None:
        expect(self.compact).to_be_visible()

    def expect_compact_hidden(self) -> None:
        expect(self.compact).to_be_hidden()

    def expect_iface_table_visible(self) -> None:
        expect(self.iface_table).to_be_visible()

    def expect_iface_table_hidden(self) -> None:
        expect(self.iface_table).to_be_hidden()

    def expect_widget_visible(self) -> None:
        expect(self.widget).to_be_visible()
