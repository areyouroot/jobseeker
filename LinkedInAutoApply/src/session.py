import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"

class LinkedInSession:
    """Handles authentication and login processes on LinkedIn."""

    def __init__(self, page, email: str, password: str, timeout: int,
                 telegram_bot=None, browser_controller=None, log_fn=print):
        self.page = page
        self.email = email
        self.password = password
        self.timeout = timeout
        self.telegram = telegram_bot
        self.browser_controller = browser_controller
        self.log_fn = log_fn

    def is_logged_in(self) -> bool:
        """Check if the current session is already logged in by navigating to feed."""
        try:
            self.log_fn("[INFO] Checking if already logged in via cookies...")
            self.page.goto(LINKEDIN_FEED_URL, wait_until="domcontentloaded", timeout=self.timeout)
            time.sleep(3)

            # If we're on the feed page, we're logged in
            current_url = self.page.url
            if "/feed" in current_url or "/mynetwork" in current_url:
                self.log_fn("[SUCCESS] Already logged in via saved cookies!")
                return True

            # Check for profile/nav elements that indicate login
            try:
                nav = self.page.locator('nav.global-nav, [data-test-global-nav]').first
                if nav.is_visible(timeout=3000):
                    self.log_fn("[SUCCESS] Already logged in via saved cookies!")
                    return True
            except Exception:
                pass

            return False
        except Exception as e:
            self.log_fn(f"[WARNING] Cookie check failed: {e}")
            return False

    def login(self) -> bool:
        """Log in to LinkedIn. Returns True on success."""
        # First check if cookies work
        if self.is_logged_in():
            return True

        self.log_fn("[INFO] Navigating to LinkedIn login page...")
        self.page.goto(LINKEDIN_LOGIN_URL, wait_until="domcontentloaded", timeout=self.timeout)
        time.sleep(2)

        # Check if we are already logged in (e.g. redirected to feed or profile)
        current_url = self.page.url
        if "/feed" in current_url or "/mynetwork" in current_url or "/in/" in current_url:
            self.log_fn("[SUCCESS] Already logged in (redirected to feed/profile)!")
            if self.browser_controller:
                self.browser_controller.save_cookies()
            return True

        try:
            nav = self.page.locator('nav.global-nav, [data-test-global-nav]').first
            if nav.is_visible(timeout=1000):
                self.log_fn("[SUCCESS] Already logged in (detected global navigation)!")
                if self.browser_controller:
                    self.browser_controller.save_cookies()
                return True
        except Exception:
            pass

        self.log_fn("[INFO] Entering email...")
        # LinkedIn uses dynamic IDs; match by input type + autocomplete attribute
        email_selectors = [
            'input[type="email"]:visible',
            'input[autocomplete*="username"]:visible',
            'input[name="session_key"]:visible',
            '#username:visible',
        ]
        email_input = None
        for sel in email_selectors:
            try:
                candidate = self.page.locator(sel).first
                if candidate.is_visible(timeout=3000):
                    email_input = candidate
                    break
            except Exception:
                continue
        if not email_input:
            raise Exception("Could not find email input on LinkedIn login page.")
        email_input.click()
        email_input.fill(self.email)

        self.log_fn("[INFO] Entering password...")
        password_selectors = [
            'input[type="password"]:visible',
            'input[autocomplete*="password"]:visible',
            'input[name="session_password"]:visible',
            '#password:visible',
        ]
        password_input = None
        for sel in password_selectors:
            try:
                candidate = self.page.locator(sel).first
                if candidate.is_visible(timeout=3000):
                    password_input = candidate
                    break
            except Exception:
                continue
        if not password_input:
            raise Exception("Could not find password input on LinkedIn login page.")
        password_input.click()
        password_input.fill(self.password)

        self.log_fn("[INFO] Clicking Sign In button...")
        # Target only the actual sign-in buttons, excluding SSO buttons
        signin_selectors = [
            'button[type="submit"]:visible',
            'button:text-is("Sign in"):visible',
            'button:has-text("Sign in"):not(:has-text("Microsoft")):not(:has-text("Apple")):visible',
            'span:text-is("Sign in"):visible',
            'span:has-text("Sign in"):not(:has-text("Microsoft")):not(:has-text("Apple")):visible',
        ]
        login_button = None
        for sel in signin_selectors:
            try:
                candidate = self.page.locator(sel).first
                if candidate.is_visible(timeout=3000):
                    login_button = candidate
                    break
            except Exception:
                continue
        if not login_button:
            raise Exception("Could not find Sign In button on LinkedIn login page.")
        login_button.click()

        self.log_fn("[INFO] Waiting for login to complete...")
        time.sleep(5)

        # Check for verification / 2FA challenge
        current_url = self.page.url
        if "checkpoint" in current_url or "challenge" in current_url:
            self.log_fn("[WARNING] ⚠ LinkedIn security challenge detected!")
            if self.telegram and self.telegram.is_configured:
                self.telegram.send_message(
                    "⚠️ <b>LinkedIn Security Challenge</b>\n\n"
                    "LinkedIn is asking for verification (CAPTCHA, email code, or phone).\n"
                    "Please complete it manually in the browser window.\n\n"
                    "<i>Waiting up to 5 minutes...</i>"
                )

            # Wait up to 5 minutes for manual verification
            self.log_fn("[INFO] Waiting up to 5 minutes for manual verification...")
            start = time.time()
            while time.time() - start < 300:
                current_url = self.page.url
                if "/feed" in current_url or "/mynetwork" in current_url:
                    break
                time.sleep(5)

        # Verify login success
        current_url = self.page.url
        if "/feed" in current_url or "/mynetwork" in current_url or "/in/" in current_url:
            self.log_fn("[SUCCESS] Logged in successfully!")
            # Save cookies for next time
            if self.browser_controller:
                self.browser_controller.save_cookies()
            return True

        # Check for error messages
        try:
            error_msg = self.page.locator('#error-for-username, #error-for-password, [class*="error"], [class*="alert"]')
            if error_msg.is_visible(timeout=2000):
                self.log_fn(f"[ERROR] Login failed: {error_msg.text_content()}")
                return False
        except Exception:
            pass

        # If URL is still on login page, login failed
        if "login" in self.page.url.lower():
            self.log_fn("[ERROR] Login failed — still on login page.")
            return False

        # Might be on a different page but logged in
        time.sleep(3)
        self.log_fn("[SUCCESS] Logged in successfully!")
        if self.browser_controller:
            self.browser_controller.save_cookies()
        return True
