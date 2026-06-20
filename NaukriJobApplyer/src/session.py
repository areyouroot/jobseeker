import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"

class NaukriSession:
    """Handles authentication and login processes on Naukri.com."""

    def __init__(self, page, email: str, password: str, timeout: int, log_fn=print):
        self.page = page
        self.email = email
        self.password = password
        self.timeout = timeout
        self.log_fn = log_fn

    def login(self) -> bool:
        """Log in to Naukri. Returns True on success."""
        self.log_fn("[INFO] Navigating to Naukri login page...")
        self.page.goto(NAUKRI_LOGIN_URL, wait_until="domcontentloaded", timeout=self.timeout)
        time.sleep(2)

        self.log_fn("[INFO] Entering email...")
        email_input = self.page.locator('#usernameField')
        email_input.wait_for(state="visible", timeout=self.timeout)
        email_input.click()
        email_input.fill(self.email)

        self.log_fn("[INFO] Entering password...")
        password_input = self.page.locator('#passwordField')
        password_input.wait_for(state="visible", timeout=self.timeout)
        password_input.click()
        password_input.fill(self.password)

        self.log_fn("[INFO] Clicking Login button...")
        login_button = self.page.locator('button[type="submit"].blue-btn')
        login_button.wait_for(state="visible", timeout=self.timeout)
        login_button.click()

        self.log_fn("[INFO] Waiting for login to complete...")
        try:
            self.page.wait_for_url("**/nlogin/login**", timeout=5000)
            error_msg = self.page.locator(".err-message, .error-msg, [class*='error']")
            if error_msg.is_visible():
                self.log_fn(f"[ERROR] Login failed: {error_msg.text_content()}")
                return False
        except PlaywrightTimeoutError:
            pass  # URL changed → login succeeded

        time.sleep(3)
        self.log_fn("[SUCCESS] Logged in successfully!")
        return True
