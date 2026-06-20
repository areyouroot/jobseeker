import json
from pathlib import Path
from playwright.sync_api import sync_playwright

class LinkedInBrowser:
    """Manages the launch, setup, and cleanup of the Playwright browser session with cookie persistence."""

    def __init__(self, slow_mo: int, timeout: int, log_fn=print):
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.log_fn = log_fn
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

        # Cookie persistence file
        self._cookies_path = Path(__file__).resolve().parent.parent / "cookies.json"

    def launch(self):
        """Start Playwright and launch a visible Chromium browser with session persistence."""
        self.log_fn("[INFO] Launching browser...")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=False,
            slow_mo=self.slow_mo,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
        )

        # Load saved storage state (cookies) if available
        storage_state = None
        if self._cookies_path.exists():
            try:
                with open(self._cookies_path, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                # Validate structure before using
                if isinstance(stored, dict) and "cookies" in stored:
                    storage_state = str(self._cookies_path)
                    self.log_fn("[INFO] Loaded saved session cookies.")
            except Exception as e:
                self.log_fn(f"[WARNING] Could not load cookies: {e}")

        context_kwargs = {
            "viewport": None,
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        if storage_state:
            context_kwargs["storage_state"] = storage_state

        self._context = self._browser.new_context(**context_kwargs)
        self._page = self._context.new_page()
        return self._page

    def save_cookies(self):
        """Save the current browser session cookies to disk."""
        try:
            if self._context:
                self._context.storage_state(path=str(self._cookies_path))
                self.log_fn("[INFO] Session cookies saved.")
        except Exception as e:
            self.log_fn(f"[WARNING] Failed to save cookies: {e}")

    def close(self):
        """Safely close contexts, browser, and stop Playwright."""
        # Save cookies before closing
        self.save_cookies()

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
