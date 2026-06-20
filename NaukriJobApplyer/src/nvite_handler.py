import time
from src.screening_handler import ScreeningHandler

NAUKRI_HOMEPAGE_URL = "https://www.naukri.com/mnjuser/homepage"

class NViteHandler:
    """Checks the homepage for recruiter invites (NVites) and accepts them."""

    def __init__(self, page, telegram_bot, timeout: int, log_fn=print):
        self.page = page
        self.telegram = telegram_bot
        self.timeout = timeout
        self.log_fn = log_fn
        self.screening_handler = ScreeningHandler(page, telegram_bot, timeout, log_fn)

    def check_and_accept_nvites(self) -> int:
        """
        Navigate to the Naukri homepage/dashboard, look for pending
        recruiter invites (NVites), and accept them. Relays pre-screening questions via Telegram.
        Returns the number of accepted invites.
        """
        self.log_fn("[INFO] 🔔 Checking for new recruiter NVites...")

        # Navigate to the homepage / dashboard where invites are shown
        self.page.goto(NAUKRI_HOMEPAGE_URL, wait_until="domcontentloaded", timeout=self.timeout)
        time.sleep(3)

        # Strategy 1: Look for notification bell / invites section
        try:
            bell = self.page.locator(
                '[class*="nI-gNb-notification"], '
                '[class*="notification-bell"], '
                'a[href*="notification"], '
                '[class*="bell"]'
            ).first
            if bell.is_visible(timeout=3000):
                bell.click()
                time.sleep(2)
                self.log_fn("[INFO] Opened notification tray.")
        except Exception:
            self.log_fn("[INFO] No notification bell found, continuing...")

        # Strategy 2: Look for invite cards / buttons on the page
        invite_selectors = [
            'button:has-text("Interested")',
            'button:has-text("Apply")',
            'a:has-text("View & Apply")',
            'button:has-text("Accept")',
            '[class*="invite"] button',
            '[class*="nvite"] button',
            '[class*="Invite"] button',
            '[class*="recommendation"] button:has-text("Apply")',
        ]

        accepted_count = 0

        for selector in invite_selectors:
            try:
                buttons = self.page.locator(selector)
                count = buttons.count()
                if count == 0:
                    continue

                self.log_fn(f"[INFO] Found {count} invite button(s) matching '{selector}'.")

                for i in range(count):
                    btn = buttons.nth(i)
                    if not btn.is_visible(timeout=2000):
                        continue

                    # Grab some context about this invite (job title, company, etc.)
                    parent_card = btn.locator(
                        "xpath=ancestor::div[contains(@class,'card') or contains(@class,'invite') or contains(@class,'recommendation')]"
                    ).first
                    invite_text = ""
                    try:
                        invite_text = parent_card.inner_text(timeout=2000)
                    except Exception:
                        try:
                            invite_text = btn.inner_text(timeout=1000)
                        except Exception:
                            invite_text = "(unknown invite)"

                    # Truncate for readability
                    invite_preview = invite_text.replace("\n", " ").strip()[:120]
                    self.log_fn(f"[INFO] 📩 Processing invite: {invite_preview}...")

                    # Notify via Telegram
                    if self.telegram.is_configured:
                        self.telegram.send_message(
                            f"📩 <b>New NVite found!</b>\n\n{invite_preview}"
                        )

                    # Click the accept / apply button
                    try:
                        btn.click()
                        time.sleep(3)
                        self.log_fn("[INFO] Clicked invite button.")
                    except Exception as click_err:
                        self.log_fn(f"[WARNING] Could not click invite: {click_err}")
                        continue

                    # Check for pre-screening question modals
                    self.screening_handler.handle_screening_questions()

                    accepted_count += 1
                    time.sleep(2)

            except Exception:
                # Selector didn't match or page changed — not an error
                continue

        if accepted_count > 0:
            self.log_fn(f"[SUCCESS] ✅ Accepted {accepted_count} NVite(s).")
            if self.telegram.is_configured:
                self.telegram.send_message(f"✅ Accepted {accepted_count} NVite(s) on Naukri.")
        else:
            self.log_fn("[INFO] No new NVites found.")

        return accepted_count
