"""Base page object shared by all Reticulum plugin pages.

Provides navigation helpers, alert locators, and spinner waits that
every page inherits.
"""

from playwright.sync_api import Page, Locator


class BasePage:
    """Common page interactions for the OPNsense Reticulum plugin."""

    SPINNER_TIMEOUT = 15_000  # ms

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    # -- Navigation ----------------------------------------------------------

    def goto(self, path: str) -> None:
        """Navigate to *path* (appended to base_url) and wait for idle."""
        self.page.goto(self.base_url + path, wait_until="networkidle")

    # -- Alerts --------------------------------------------------------------

    def get_success_alert(self) -> Locator:
        """Locator for a Bootstrap success alert on the page."""
        return self.page.locator(".alert-success")

    def get_error_alert(self) -> Locator:
        """Locator for a Bootstrap danger alert on the page."""
        return self.page.locator(".alert-danger")

    # -- Spinner -------------------------------------------------------------

    def wait_for_spinner_gone(self) -> None:
        """Wait for the OPNsense AJAX spinner to disappear."""
        spinner = self.page.locator(".fa-spinner")
        # Only wait if the spinner is currently visible; avoids timing out
        # when no spinner was shown at all.
        if spinner.count() > 0:
            spinner.first.wait_for(state="hidden", timeout=self.SPINNER_TIMEOUT)

    # -- Page header ---------------------------------------------------------

    def page_title(self) -> str:
        """Return the text of the breadcrumb heading element."""
        return self.page.locator(".page-content-head h1, .content-heading h1").first.inner_text()
