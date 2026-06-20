from playwright.sync_api import sync_playwright

class NaukriBrowser:
    """Manages the launch, setup, and cleanup of the Playwright browser session."""

    def __init__(self, slow_mo: int, timeout: int, log_fn=print):
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.log_fn = log_fn
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def launch(self):
        """Start Playwright and launch a visible Chromium browser with user-agent spoofing."""
        self.log_fn("[INFO] Launching browser...")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=False,
            slow_mo=self.slow_mo,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
        )
        self._context = self._browser.new_context(
            viewport=None,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = self._context.new_page()
        return self._page

    def close(self):
        """Safely close contexts, browser, and stop Playwright."""
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self.log_fn("[INFO] Browser closed.")

    def __enter__(self):
        return self.launch()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
