"""Page object for the Reticulum Log Viewer page.

URL: /ui/reticulum/logs
"""

from playwright.sync_api import Page, Locator, expect

from .base_page import BasePage


class LogsPage(BasePage):
    """Interactions and assertions for /ui/reticulum/logs."""

    PATH = "/ui/reticulum/logs"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)

    # -- Navigation ----------------------------------------------------------

    def navigate(self) -> None:
        """Open the logs page and wait for the tab strip."""
        self.goto(self.PATH)
        self.page.wait_for_selector(
            "#log-tabs", state="visible", timeout=self.PAGE_READY_TIMEOUT
        )

    # -- Tab locators --------------------------------------------------------

    @property
    def rnsd_tab(self) -> Locator:
        return self.page.locator('#log-tabs a[data-service="rnsd"]')

    @property
    def lxmd_tab(self) -> Locator:
        return self.page.locator('#log-tabs a[data-service="lxmd"]')

    def click_rnsd_tab(self) -> None:
        self.rnsd_tab.click()
        self.wait_for_spinner_gone()

    def click_lxmd_tab(self) -> None:
        self.lxmd_tab.click()
        self.wait_for_spinner_gone()

    # -- Filter controls -----------------------------------------------------

    @property
    def severity_filter(self) -> Locator:
        return self.page.locator("#log-level")

    @property
    def keyword_filter(self) -> Locator:
        return self.page.locator("#log-search")

    @property
    def lines_select(self) -> Locator:
        return self.page.locator("#log-lines")

    def set_severity_filter(self, level: str) -> None:
        """Select severity filter by option value (empty string for All)."""
        self.severity_filter.select_option(value=level)

    def set_keyword_filter(self, keyword: str) -> None:
        self.keyword_filter.fill(keyword)

    def set_lines_count(self, count: str) -> None:
        """Select lines-to-fetch by option value."""
        self.lines_select.select_option(value=count)

    # -- Action buttons ------------------------------------------------------

    @property
    def refresh_btn(self) -> Locator:
        return self.page.locator("#refresh-logs")

    @property
    def download_btn(self) -> Locator:
        return self.page.locator("#download-logs")

    @property
    def auto_refresh_checkbox(self) -> Locator:
        return self.page.locator("#auto-refresh")

    def click_refresh(self) -> None:
        self.refresh_btn.click()
        self.wait_for_spinner_gone()

    def click_download(self) -> None:
        self.download_btn.click()

    def toggle_auto_refresh(self) -> None:
        self.auto_refresh_checkbox.click()

    def auto_refresh_active(self) -> bool:
        return self.auto_refresh_checkbox.is_checked()

    # -- Output area ---------------------------------------------------------

    @property
    def log_loading(self) -> Locator:
        return self.page.locator("#log-loading")

    @property
    def log_empty_service(self) -> Locator:
        return self.page.locator("#log-empty-service")

    @property
    def log_empty_filter(self) -> Locator:
        return self.page.locator("#log-empty-filter")

    @property
    def log_output(self) -> Locator:
        return self.page.locator("#log-output")

    def log_line_count(self) -> int:
        """Return the number of non-empty lines in the log output."""
        text = self.log_output.inner_text()
        if not text.strip():
            return 0
        return len([line for line in text.split("\n") if line.strip()])

    def log_lines(self) -> list:
        """Return all non-empty log lines as a list of strings."""
        text = self.log_output.inner_text()
        return [line for line in text.split("\n") if line.strip()]

    # -- Assertion helpers ---------------------------------------------------

    def expect_loading_visible(self) -> None:
        expect(self.log_loading).to_be_visible()

    def expect_log_output_visible(self) -> None:
        expect(self.log_output).to_be_visible()

    def expect_empty_service_visible(self) -> None:
        expect(self.log_empty_service).to_be_visible()

    def expect_empty_filter_visible(self) -> None:
        expect(self.log_empty_filter).to_be_visible()
