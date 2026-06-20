import time
import urllib.parse
from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

class JobApplier:
    """Searches for jobs on Naukri by keywords and automates the application process."""

    def __init__(self, page, telegram_bot, apply_delay: int, timeout: int, log_fn=print):
        self.page = page
        self.telegram = telegram_bot
        self.apply_delay = apply_delay
        self.timeout = timeout
        self.log_fn = log_fn
        self.total_applied = 0
        self.applied_details = {}

    def apply_for_jobs(self, keywords: list[str]):
        """For each keyword, search and apply to 3 jobs (max 15 overall)."""
        self.log_fn(f"[INFO] Starting automated job search for keywords: {', '.join(keywords)}")
        self.total_applied = 0
        self.applied_details = {}

        for keyword in keywords:
            if self.total_applied >= 15:
                self.log_fn("[INFO] Session limit of 15 successful applications reached. Stopping.")
                break

            self.log_fn(f"[INFO] 🔍 Processing search keyword: '{keyword}'...")
            try:
                # 1. Navigate to Search Page
                search_url = f"https://www.naukri.com/jobs-in-india?k={urllib.parse.quote(keyword)}"
                self.page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout)
                time.sleep(4)

                # 2. Extract Job Links
                links = self.page.locator('a[href*="/job-description/"]')
                count = links.count()
                if count == 0:
                    links = self.page.locator('a.title, a.jobTupleTitle')
                    count = links.count()

                job_urls = []
                for i in range(count):
                    href = links.nth(i).get_attribute("href")
                    if href:
                        if href.startswith("/"):
                            href = "https://www.naukri.com" + href
                        if href not in job_urls:
                            job_urls.append(href)

                self.log_fn(f"[INFO] Found {len(job_urls)} job(s) for keyword '{keyword}'.")
                
                # 3. Process each job link (target 3 successful applications per keyword)
                success_count = 0
                self.applied_details[keyword] = 0
                for job_url in job_urls:
                    if success_count >= 3:
                        self.log_fn(f"[SUCCESS] Applied to 3 jobs for '{keyword}'. Moving to next keyword.")
                        break

                    if self.total_applied >= 15:
                        self.log_fn("[INFO] Limit of 15 successful applications reached. Stopping.")
                        return

                    try:
                        applied = self._apply_single_job(job_url, keyword)
                        if applied:
                            success_count += 1
                            self.applied_details[keyword] += 1
                    except Exception as e:
                        self.log_fn(f"[ERROR] Failed to apply for {job_url}: {e}")
                        self._handle_failure(e)

            except Exception as e:
                self.log_fn(f"[ERROR] Error during job search for keyword '{keyword}': {e}")
                self._handle_failure(e)

    def _apply_single_job(self, job_url: str, keyword: str) -> bool:
        """Navigate to single job description and apply."""
        self.log_fn(f"[INFO] Navigating to job: {job_url}")
        self.page.goto(job_url, wait_until="domcontentloaded", timeout=self.timeout)
        time.sleep(3)

        # 1. Check if already applied first
        applied_selectors = [
            'text="Applied"',
            'text="Already Applied"',
            'button:has-text("Applied")',
            'button:has-text("Already Applied")'
        ]
        already_applied = False
        for selector in applied_selectors:
            try:
                if self.page.locator(selector).first.is_visible(timeout=1000):
                    already_applied = True
                    break
            except Exception:
                continue

        if already_applied:
            self.log_fn("[INFO] Already applied to this job. Skipping.")
            return False

        # 2. Look for the Apply button
        apply_selectors = [
            'button:has-text("Apply")',
            'button:has-text("Apply Now")',
            'button:has-text("Apply on company site")',
            'button:has-text("Apply on company website")',
            'a:has-text("Apply")',
            '.apply-button',
            '#apply-button',
            '[class*="apply"] button',
            '[class*="Apply"] button'
        ]

        apply_btn = None
        for selector in apply_selectors:
            try:
                candidate = self.page.locator(selector).first
                if candidate.is_visible(timeout=1500):
                    apply_btn = candidate
                    break
            except Exception:
                continue

        if not apply_btn:
            raise Exception("Apply button not found on job description page.")

        # Click and handle popup redirects
        try:
            with self.page.context.expect_page(timeout=5000) as new_page_info:
                apply_btn.click()
            
            # A new tab opened -> External career site
            new_page = new_page_info.value
            new_page.wait_for_load_state("domcontentloaded")
            external_url = new_page.url
            self.log_fn(f"[INFO] External redirect detected: {external_url}")
            
            if self.telegram.is_configured:
                self.telegram.send_message(
                    f"🔗 <b>External Job Link</b>\n"
                    f"Keyword: <code>{keyword}</code>\n"
                    f"This job redirects to an external site. Please apply manually:\n"
                    f"<a href='{external_url}'>{external_url}</a>"
                )
            new_page.close()
            time.sleep(2)
            # Skip since it redirects to external
            return False
        except PlaywrightTimeoutError:
            # No new tab opened
            time.sleep(3)
            # Check if main page URL redirected
            if "naukri.com" not in self.page.url:
                external_url = self.page.url
                self.log_fn(f"[INFO] Page redirected to external site: {external_url}")
                if self.telegram.is_configured:
                    self.telegram.send_message(
                        f"🔗 <b>External Job Link</b>\n"
                        f"Keyword: <code>{keyword}</code>\n"
                        f"This job redirected to an external site. Please apply manually:\n"
                        f"<a href='{external_url}'>{external_url}</a>"
                    )
                # Recover page state by navigating back to Naukri
                self.page.goto("https://www.naukri.com", wait_until="domcontentloaded", timeout=self.timeout)
                time.sleep(2)
                return False

        # Check for pre-screening question modal
        modal_selectors = [
            '[class*="modal"]',
            '[class*="Modal"]',
            '[class*="dialog"]',
            '[class*="Dialog"]',
            '[class*="screening"]',
            '[class*="chatbot"]',
            '[class*="question"]',
            '[role="dialog"]',
        ]

        modal = None
        for sel in modal_selectors:
            try:
                candidate = self.page.locator(sel).first
                if candidate.is_visible(timeout=1500):
                    modal = candidate
                    break
            except Exception:
                continue

        if modal:
            # Check if modal indicates that the job is already applied, closed, expired, or limit reached
            try:
                modal_text = modal.inner_text(timeout=2000).lower()
                skip_keywords = ["already applied", "previously applied", "limit reached", "limit exceeded", "expired", "closed"]
                if any(kw in modal_text for kw in skip_keywords):
                    self.log_fn(f"[INFO] Skip popup/modal detected: '{modal_text.strip()[:100]}...'. Skipping.")
                    try:
                        self.page.keyboard.press("Escape")
                        close_btn = modal.locator('[class*="close"], [class*="Close"], text="✕"').first
                        if close_btn.is_visible(timeout=1000):
                            close_btn.click()
                    except Exception:
                        pass
                    return False
            except Exception as e:
                self.log_fn(f"[WARNING] Error checking modal text: {e}")

            # Find labels and inputs inside modal
            questions = modal.locator(
                'label, [class*="question"], [class*="Question"], [class*="label"], p:near(input), p:near(textarea)'
            )
            inputs = modal.locator(
                'input[type="text"], input[type="number"], textarea, select, input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])'
            )
            
            q_count = questions.count()
            i_count = inputs.count()
            pairs = min(q_count, i_count)
            
            has_solo_input = False
            try:
                solo_input = modal.locator('textarea, input[type="text"]').first
                if solo_input.is_visible(timeout=1500):
                    has_solo_input = True
            except Exception:
                pass

            if pairs == 0 and not has_solo_input:
                self.log_fn("[INFO] Info/Success modal detected (no questions). Closing modal.")
                try:
                    self.page.keyboard.press("Escape")
                    close_btn = modal.locator('[class*="close"], [class*="Close"], text="✕"').first
                    if close_btn.is_visible(timeout=1000):
                        close_btn.click()
                except Exception:
                    pass
            else:
                self.log_fn("[INFO] 📝 Screening questions detected! Relaying to Telegram...")
                timed_out = False
                
                if pairs == 0:
                    # Solo text area
                    try:
                        solo_input = modal.locator('textarea, input[type="text"]').first
                        if solo_input.is_visible(timeout=1500):
                            modal_text = modal.inner_text(timeout=2000)
                            question_text = modal_text.replace("\n", " ").strip()[:300]
                            self.log_fn(f"[INFO] Question: {question_text}")
                            
                            if self.telegram.is_configured:
                                # 2 hours timeout = 7200 seconds
                                answer = self.telegram.ask_question(question_text, timeout_seconds=7200)
                                if answer:
                                    solo_input.fill(answer)
                                else:
                                    timed_out = True
                            else:
                                self.log_fn("[WARNING] Telegram not configured — skipping question.")
                                timed_out = True
                    except Exception:
                        pass
                else:
                    for idx in range(pairs):
                        try:
                            q_label = questions.nth(idx).inner_text(timeout=2000).strip()
                            inp = inputs.nth(idx)
                            
                            if not q_label or not inp.is_visible(timeout=1500):
                                continue
                                
                            self.log_fn(f"[INFO] Question {idx+1}: {q_label}")
                            
                            if self.telegram.is_configured:
                                # 2 hours timeout
                                answer = self.telegram.ask_question(q_label, timeout_seconds=7200)
                                if answer:
                                    tag = inp.evaluate("el => el.tagName.toLowerCase()")
                                    if tag == "select":
                                        inp.select_option(label=answer)
                                    else:
                                        inp.fill(answer)
                                else:
                                    timed_out = True
                                    break
                            else:
                                self.log_fn("[WARNING] Telegram not configured — cannot answer.")
                                timed_out = True
                                break
                        except Exception as qe:
                            self.log_fn(f"[WARNING] Error answering question {idx+1}: {qe}")
                            
                if timed_out:
                    self.log_fn("[WARNING] ⏳ Telegram response timed out (2 hours limit). Skipping job.")
                    # Attempt to close the modal
                    try:
                        self.page.keyboard.press("Escape")
                        close_btn = modal.locator('[class*="close"], [class*="Close"], text="✕"').first
                        if close_btn.is_visible(timeout=1000):
                            close_btn.click()
                    except Exception:
                        pass
                    return False  # Skip to the next job

                # Submit modal answers
                submit_selectors = [
                    'button:has-text("Submit")',
                    'button:has-text("Apply")',
                    'button:has-text("Send")',
                    'button[type="submit"]',
                    'input[type="submit"]'
                ]
                submitted = False
                for sel in submit_selectors:
                    try:
                        submit_btn = modal.locator(sel).first
                        if submit_btn.is_visible(timeout=1500):
                            submit_btn.click()
                            self.log_fn("[SUCCESS] Submitted screening answers.")
                            time.sleep(3)
                            submitted = True
                            break
                    except Exception:
                        continue
                        
                if not submitted:
                    raise Exception("Submit button not found inside questions modal.")

        # Success check & logging
        time.sleep(3)
        self.total_applied += 1
        self.log_fn(f"[SUCCESS] ✅ Successfully applied! Total applied: {self.total_applied}/15.")
        
        if self.telegram.is_configured:
            self.telegram.send_message(
                f"✅ <b>Job Applied</b>\n"
                f"Keyword: <code>{keyword}</code>\n"
                f"Successfully applied to:\n"
                f"{job_url}"
            )

        # Apply configurable delay
        self.log_fn(f"[INFO] Sleeping for {self.apply_delay} seconds (apply delay)...")
        time.sleep(self.apply_delay)
        return True

    def _handle_failure(self, error):
        """Take screenshot and upload to Telegram on failure."""
        try:
            screenshot_path = "screenshot.png"
            self.page.screenshot(path=screenshot_path)
            self.log_fn(f"[INFO] Screenshot saved to {screenshot_path}")
            
            if self.telegram.is_configured:
                caption = f"🚨 Naukri Job Application failure alert:\n{str(error)[:150]}"
                self.telegram.send_photo(screenshot_path, caption=caption)
        except Exception as s_err:
            self.log_fn(f"[ERROR] Failed to take/send screenshot: {s_err}")
