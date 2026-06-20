import re
import time
import urllib.parse
from pathlib import Path
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from src.automation.applied_tracker import AppliedTracker

class JobApplier:
    """Searches for jobs on LinkedIn and automates the Easy Apply process."""

    def __init__(self, page, telegram_bot, apply_delay: int, timeout: int,
                 max_applications: int = 25, resume_path: str = "",
                 filters: dict = None, log_fn=print):
        self.page = page
        self.telegram = telegram_bot
        self.apply_delay = apply_delay
        self.timeout = timeout
        self.max_applications = max_applications
        self.resume_path = resume_path
        self.filters = filters or {}
        self.log_fn = log_fn
        self.total_applied = 0
        self.applied_details = {}
        self.tracker = AppliedTracker(log_fn=log_fn)

    def apply_for_jobs(self, keywords: list[str]):
        """For each keyword, search and apply to Easy Apply jobs."""
        self.log_fn(f"[INFO] Starting LinkedIn Easy Apply for keywords: {', '.join(keywords)}")
        self.total_applied = 0
        self.applied_details = {}

        for keyword in keywords:
            if self.total_applied >= self.max_applications:
                self.log_fn(f"[INFO] Session limit of {self.max_applications} applications reached. Stopping.")
                break

            self.log_fn(f"[INFO] 🔍 Processing search keyword: '{keyword}'...")
            try:
                # 1. Navigate to LinkedIn Jobs search with Easy Apply filter
                search_url = self._build_search_url(keyword)
                self.page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout)
                time.sleep(4)

                # 2. Scroll to load more job cards
                self._scroll_job_list()

                # 3. Extract job card elements from the sidebar
                job_cards = self._extract_job_cards()
                self.log_fn(f"[INFO] Found {len(job_cards)} job(s) for keyword '{keyword}'.")

                # 4. Process each job card
                success_count = 0
                self.applied_details[keyword] = 0
                for job_info in job_cards:
                    if success_count >= 5:
                        self.log_fn(f"[SUCCESS] Applied to 5 jobs for '{keyword}'. Moving to next keyword.")
                        break

                    if self.total_applied >= self.max_applications:
                        self.log_fn(f"[INFO] Limit of {self.max_applications} applications reached. Stopping.")
                        return

                    try:
                        applied = self._apply_single_job(job_info, keyword)
                        if applied:
                            success_count += 1
                            self.applied_details[keyword] += 1
                    except Exception as e:
                        self.log_fn(f"[ERROR] Failed to apply for job: {e}")
                        self._handle_failure(e)

            except Exception as e:
                self.log_fn(f"[ERROR] Error during job search for keyword '{keyword}': {e}")
                self._handle_failure(e)

    def _build_search_url(self, keyword: str) -> str:
        """Build LinkedIn Jobs search URL with Easy Apply filter."""
        params = {
            "keywords": keyword,
            "f_AL": "true",  # Easy Apply filter
        }

        # Add optional filters
        if self.filters.get("location"):
            params["location"] = self.filters["location"]

        if self.filters.get("date_posted"):
            date_map = {
                "past 24 hours": "r86400",
                "past week": "r604800",
                "past month": "r2592000",
            }
            date_val = date_map.get(self.filters["date_posted"].lower(), "")
            if date_val:
                params["f_TPR"] = date_val

        if self.filters.get("experience_level"):
            exp_map = {
                "internship": "1",
                "entry level": "2",
                "associate": "3",
                "mid-senior level": "4",
                "director": "5",
                "executive": "6",
            }
            levels = [l.strip().lower() for l in self.filters["experience_level"].split(",")]
            exp_ids = [exp_map[l] for l in levels if l in exp_map]
            if exp_ids:
                params["f_E"] = ",".join(exp_ids)

        if self.filters.get("remote"):
            remote_map = {
                "on-site": "1",
                "remote": "2",
                "hybrid": "3",
            }
            remote_val = remote_map.get(self.filters["remote"].lower(), "")
            if remote_val:
                params["f_WT"] = remote_val

        query = urllib.parse.urlencode(params)
        return f"https://www.linkedin.com/jobs/search/?{query}"

    def _scroll_job_list(self):
        """Scroll the job list sidebar to load more results."""
        try:
            jobs_container = self.page.locator('.jobs-search-results-list, .scaffold-layout__list')
            if jobs_container.count() > 0:
                for _ in range(3):
                    jobs_container.first.evaluate("el => el.scrollTop = el.scrollHeight")
                    time.sleep(1)
        except Exception:
            pass

    def _extract_job_cards(self) -> list[dict]:
        """Extract job card info from the search results sidebar."""
        job_cards = []

        # LinkedIn job cards in search results
        card_selectors = [
            '.job-card-container',
            '.jobs-search-results__list-item',
            'li.ember-view.occludable-update',
            '.scaffold-layout__list-item',
        ]

        cards = None
        for sel in card_selectors:
            candidates = self.page.locator(sel)
            if candidates.count() > 0:
                cards = candidates
                break

        if not cards or cards.count() == 0:
            # Fallback: try to get job links directly
            links = self.page.locator('a[href*="/jobs/view/"]')
            count = links.count()
            for i in range(min(count, 25)):
                try:
                    href = links.nth(i).get_attribute("href")
                    if href:
                        job_id = self._extract_job_id(href)
                        if job_id and not self.tracker.is_applied(job_id):
                            job_cards.append({
                                "id": job_id,
                                "url": href if href.startswith("http") else f"https://www.linkedin.com{href}",
                                "title": "",
                                "company": "",
                                "element_index": i,
                            })
                except Exception:
                    continue
            return job_cards

        count = cards.count()
        for i in range(min(count, 25)):
            try:
                card = cards.nth(i)

                # Extract job link
                link = card.locator('a[href*="/jobs/view/"]').first
                href = link.get_attribute("href") if link.count() > 0 else ""
                if not href:
                    continue

                job_id = self._extract_job_id(href)
                if not job_id:
                    continue

                # Skip if already applied (from tracker)
                if self.tracker.is_applied(job_id):
                    continue

                # Extract title and company
                title = ""
                company = ""
                try:
                    title_el = card.locator('.job-card-list__title, .artdeco-entity-lockup__title, a.job-card-container__link strong').first
                    title = title_el.inner_text(timeout=1500).strip() if title_el.count() > 0 else ""
                except Exception:
                    pass

                try:
                    company_el = card.locator('.job-card-container__primary-description, .artdeco-entity-lockup__subtitle, .job-card-container__company-name').first
                    company = company_el.inner_text(timeout=1500).strip() if company_el.count() > 0 else ""
                except Exception:
                    pass

                job_cards.append({
                    "id": job_id,
                    "url": href if href.startswith("http") else f"https://www.linkedin.com{href}",
                    "title": title,
                    "company": company,
                    "element_index": i,
                })
            except Exception:
                continue

        return job_cards

    def _extract_job_id(self, url: str) -> str:
        """Extract the numeric job ID from a LinkedIn job URL."""
        match = re.search(r'/jobs/view/(\d+)', url)
        if match:
            return match.group(1)
        # Try query parameter
        match = re.search(r'currentJobId=(\d+)', url)
        if match:
            return match.group(1)
        return ""

    def _apply_single_job(self, job_info: dict, keyword: str) -> bool:
        """Click on a job card, then apply via Easy Apply."""
        job_id = job_info["id"]
        job_url = job_info["url"]
        title = job_info.get("title", "Unknown")
        company = job_info.get("company", "Unknown")

        self.log_fn(f"[INFO] Navigating to job: {title} at {company} (ID: {job_id})")

        # Navigate to the job page
        self.page.goto(job_url, wait_until="domcontentloaded", timeout=self.timeout)
        time.sleep(3)

        # 1. Check if already applied
        already_applied_selectors = [
            'span:has-text("Applied"):visible',
            'button:has-text("Applied"):visible',
            '.artdeco-inline-feedback:has-text("Applied"):visible',
            'li-icon[type="success-pebble-icon"]:visible',
        ]
        for selector in already_applied_selectors:
            try:
                if self.page.locator(selector).first.is_visible(timeout=1500):
                    self.log_fn("[INFO] Already applied to this job. Skipping.")
                    self.tracker.mark_applied(job_id, title, company)
                    return False
            except Exception:
                continue

        # 2. Find the Easy Apply button
        easy_apply_selectors = [
            'span:text-is("Easy Apply"):visible',
            'button:text-is("Easy Apply"):visible',
            'a:text-is("Easy Apply"):visible',
            'span:has-text("Easy Apply"):visible',
            'button:has-text("Easy Apply"):visible',
            'a:has-text("Easy Apply"):visible',
            '[aria-label*="Easy Apply"]:visible',
            'button.jobs-apply-button:visible',
        ]

        easy_apply_btn = None
        for selector in easy_apply_selectors:
            try:
                candidate = self.page.locator(selector).first
                if candidate.is_visible(timeout=2000):
                    btn_text = candidate.inner_text(timeout=1000).strip().lower()
                    # Only click if it says "Easy Apply" (not external "Apply")
                    if "easy" in btn_text:
                        easy_apply_btn = candidate
                        break
            except Exception:
                continue

        if not easy_apply_btn:
            self.log_fn("[INFO] No Easy Apply button found. Skipping (external application).")
            return False

        # 3. Click Easy Apply
        self.log_fn("[INFO] 🚀 Clicking Easy Apply button...")
        easy_apply_btn.click()
        time.sleep(2)

        # 4. Handle the multi-step Easy Apply modal
        success = self._handle_easy_apply_modal(job_id, title, company, keyword)

        if success:
            self.total_applied += 1
            self.tracker.mark_applied(job_id, title, company)
            self.log_fn(f"[SUCCESS] ✅ Applied to '{title}' at '{company}'! Total: {self.total_applied}/{self.max_applications}")

            if self.telegram and self.telegram.is_configured:
                self.telegram.send_message(
                    f"✅ <b>LinkedIn Job Applied</b>\n"
                    f"Keyword: <code>{keyword}</code>\n"
                    f"Title: {title}\n"
                    f"Company: {company}\n"
                    f"Total: {self.total_applied}/{self.max_applications}"
                )

            # Apply configurable delay
            self.log_fn(f"[INFO] Sleeping for {self.apply_delay} seconds (apply delay)...")
            time.sleep(self.apply_delay)

        return success

    def _handle_easy_apply_modal(self, job_id: str, title: str, company: str, keyword: str) -> bool:
        """Handle LinkedIn's multi-step Easy Apply modal wizard."""
        max_steps = 10  # Safety limit to prevent infinite loops

        for step in range(max_steps):
            time.sleep(2)

            # Check if modal is still open
            modal = None
            modal_selectors = [
                '.jobs-easy-apply-modal:visible',
                '.jobs-easy-apply-content:visible',
                '[data-test-modal]:visible',
                '.artdeco-modal:visible',
            ]
            for sel in modal_selectors:
                try:
                    candidate = self.page.locator(sel).first
                    if candidate.is_visible(timeout=2000):
                        modal = candidate
                        break
                except Exception:
                    continue

            if not modal:
                # Modal closed — check if we see a success state
                try:
                    success_indicators = [
                        'span:has-text("Applied"):visible',
                        '.artdeco-inline-feedback:has-text("Applied"):visible',
                        'h2:has-text("Your application was sent"):visible',
                        '[data-test-artdeco-toast]:has-text("applied"):visible',
                    ]
                    for sel in success_indicators:
                        if self.page.locator(sel).first.is_visible(timeout=2000):
                            return True
                except Exception:
                    pass
                self.log_fn("[WARNING] Easy Apply modal disappeared unexpectedly.")
                return False

            # Check for "Application submitted" success page inside modal
            try:
                success_headings = modal.locator('h2, h3, [class*="post-apply"], [class*="success"]')
                for i in range(success_headings.count()):
                    text = success_headings.nth(i).inner_text(timeout=1000).lower()
                    if "application" in text and ("sent" in text or "submitted" in text):
                        self.log_fn("[INFO] Application submitted successfully!")
                        # Close the success modal
                        self._close_modal(modal)
                        return True
            except Exception:
                pass

            # Check for safety-net close/error states
            try:
                modal_text = modal.inner_text(timeout=2000).lower()
                skip_keywords = ["already applied", "previously applied", "limit reached",
                                 "limit exceeded", "expired", "closed", "no longer accepting"]
                if any(kw in modal_text for kw in skip_keywords):
                    self.log_fn(f"[INFO] Skip condition detected in modal. Skipping.")
                    self._close_modal(modal)
                    return False
            except Exception:
                pass

            # Handle resume upload step (if needed)
            self._handle_resume_step(modal)

            # Handle form fields / additional questions
            self._handle_form_fields(modal, keyword)

            # Look for action buttons: Submit, Next, Review
            submitted = self._click_next_or_submit(modal)
            if submitted == "submitted":
                # Final submit was clicked
                time.sleep(3)
                # Check for success state
                try:
                    for sel in ['h2:has-text("Your application was sent"):visible',
                                'h2:has-text("application was submitted"):visible',
                                '[class*="post-apply"]:visible']:
                        if self.page.locator(sel).first.is_visible(timeout=3000):
                            self.log_fn("[INFO] Application confirmed submitted!")
                            self._close_modal(None)
                            return True
                except Exception:
                    pass
                # Assume success if modal closed
                try:
                    if not modal.is_visible(timeout=2000):
                        return True
                except Exception:
                    return True
                return True
            elif submitted == "next":
                # Moved to next step
                self.log_fn(f"[INFO] Moved to next step ({step + 2})...")
                continue
            elif submitted == "review":
                self.log_fn("[INFO] Moved to review step...")
                continue
            else:
                # No action button found
                self.log_fn("[WARNING] No Next/Submit button found in modal step. Aborting.")
                self._close_modal(modal)
                return False

        self.log_fn("[WARNING] Exceeded max steps for Easy Apply modal. Aborting.")
        self._close_modal(None)
        return False

    def _handle_resume_step(self, modal):
        """Upload resume if the current step shows a resume upload section."""
        try:
            # Check if there's a resume upload input
            file_input = modal.locator('input[type="file"]').first
            if file_input.count() > 0 and self.resume_path:
                resume_file = Path(self.resume_path)
                if resume_file.exists():
                    # Check if a resume is already selected
                    existing_resume = modal.locator('[class*="resume"], [class*="document"]')
                    if existing_resume.count() > 0:
                        try:
                            resume_text = existing_resume.first.inner_text(timeout=1000)
                            if resume_text.strip():
                                self.log_fn("[INFO] Resume already attached. Skipping upload.")
                                return
                        except Exception:
                            pass

                    self.log_fn("[INFO] Uploading resume...")
                    file_input.set_input_files(str(resume_file))
                    time.sleep(2)
                    self.log_fn("[SUCCESS] Resume uploaded.")
        except Exception:
            pass  # No file input or upload not needed

    def _handle_form_fields(self, modal, keyword: str):
        """Fill in form fields and additional questions in the current modal step."""
        try:
            # Find all visible form groups
            form_groups = modal.locator('.fb-dash-form-element, .jobs-easy-apply-form-section__grouping, [class*="form-component"]')
            count = form_groups.count()

            if count == 0:
                return

            for i in range(count):
                try:
                    group = form_groups.nth(i)
                    if not group.is_visible(timeout=1000):
                        continue

                    # Find label
                    label = ""
                    try:
                        label_el = group.locator('label, .fb-dash-form-element__label, span[class*="label"]').first
                        label = label_el.inner_text(timeout=1000).strip() if label_el.count() > 0 else ""
                    except Exception:
                        pass

                    # Find input
                    input_el = None
                    input_type = ""

                    # Text input
                    text_input = group.locator('input[type="text"], input[type="number"], input[type="tel"], input[type="email"]').first
                    if text_input.count() > 0 and text_input.is_visible(timeout=500):
                        # Skip if already filled
                        current_val = text_input.input_value()
                        if current_val.strip():
                            continue
                        input_el = text_input
                        input_type = "text"

                    # Textarea
                    if not input_el:
                        textarea = group.locator('textarea').first
                        if textarea.count() > 0 and textarea.is_visible(timeout=500):
                            current_val = textarea.input_value()
                            if current_val.strip():
                                continue
                            input_el = textarea
                            input_type = "textarea"

                    # Select dropdown
                    if not input_el:
                        select = group.locator('select').first
                        if select.count() > 0 and select.is_visible(timeout=500):
                            # Check if already has a non-default value
                            current_val = select.input_value()
                            if current_val and current_val != "Select an option":
                                continue
                            input_el = select
                            input_type = "select"

                    # Radio buttons
                    if not input_el:
                        radios = group.locator('input[type="radio"]')
                        if radios.count() > 0:
                            # Check if any is already selected
                            already_selected = False
                            for r in range(radios.count()):
                                if radios.nth(r).is_checked():
                                    already_selected = True
                                    break
                            if already_selected:
                                continue
                            input_el = radios
                            input_type = "radio"

                    if not input_el or not label:
                        continue

                    self.log_fn(f"[INFO] 📝 Question: {label}")

                    # Try to get answer from Telegram
                    answer = None
                    if self.telegram and self.telegram.is_configured:
                        answer = self.telegram.ask_question(label, timeout_seconds=7200)

                    if answer:
                        if input_type in ("text", "textarea"):
                            input_el.fill(answer)
                            self.log_fn(f"[INFO] Filled: {answer}")
                        elif input_type == "select":
                            try:
                                input_el.select_option(label=answer)
                                self.log_fn(f"[INFO] Selected: {answer}")
                            except Exception:
                                # Try by value
                                try:
                                    input_el.select_option(value=answer)
                                except Exception:
                                    self.log_fn(f"[WARNING] Could not select option: {answer}")
                        elif input_type == "radio":
                            # Try to find radio with matching label text
                            try:
                                radio_label = group.locator(f'label:has-text("{answer}")').first
                                if radio_label.count() > 0:
                                    radio_label.click()
                                    self.log_fn(f"[INFO] Selected radio: {answer}")
                                else:
                                    # Click first option as fallback
                                    input_el.first.click()
                            except Exception:
                                pass
                    else:
                        self.log_fn(f"[WARNING] No answer received for question: {label}")

                except Exception as e:
                    self.log_fn(f"[WARNING] Error processing form field: {e}")
                    continue

        except Exception as e:
            self.log_fn(f"[WARNING] Error handling form fields: {e}")

    def _click_next_or_submit(self, modal) -> str:
        """Click the appropriate action button. Returns 'submitted', 'next', 'review', or ''."""

        # Check for "Submit application" first (final step)
        submit_selectors = [
            'button[aria-label="Submit application"]:visible',
            'button:has-text("Submit application"):visible',
            'button:has-text("Submit"):visible',
            'span:text-is("Submit application"):visible',
            'span:text-is("Submit"):visible',
            'span:has-text("Submit"):visible',
        ]
        for sel in submit_selectors:
            try:
                btn = modal.locator(sel).first
                if btn.is_visible(timeout=1500):
                    btn_text = btn.inner_text(timeout=1000).strip().lower()
                    if "submit" in btn_text:
                        self.log_fn("[INFO] 🎯 Clicking Submit application...")
                        btn.click()
                        time.sleep(3)
                        return "submitted"
            except Exception:
                continue

        # Check for "Review" button
        review_selectors = [
            'button[aria-label="Review your application"]:visible',
            'button:has-text("Review"):visible',
        ]
        for sel in review_selectors:
            try:
                btn = modal.locator(sel).first
                if btn.is_visible(timeout=1500):
                    self.log_fn("[INFO] Clicking Review...")
                    btn.click()
                    time.sleep(2)
                    return "review"
            except Exception:
                continue

        # Check for "Next" button
        next_selectors = [
            'button[aria-label="Continue to next step"]:visible',
            'button:has-text("Next"):visible',
            'footer button.artdeco-button--primary:visible',
        ]
        for sel in next_selectors:
            try:
                btn = modal.locator(sel).first
                if btn.is_visible(timeout=1500):
                    self.log_fn("[INFO] Clicking Next...")
                    btn.click()
                    time.sleep(2)
                    return "next"
            except Exception:
                continue

        return ""

    def _close_modal(self, modal):
        """Close the Easy Apply modal."""
        try:
            # Try dismiss button
            dismiss_selectors = [
                'button[aria-label="Dismiss"]:visible',
                'button[data-test-modal-close-btn]:visible',
                '.artdeco-modal__dismiss:visible',
                'button:has-text("Discard"):visible',
            ]
            for sel in dismiss_selectors:
                try:
                    btn = self.page.locator(sel).first
                    if btn.is_visible(timeout=1500):
                        btn.click()
                        time.sleep(1)

                        # Handle "Discard application?" confirmation (only click Discard, never Save)
                        try:
                            discard_btn = self.page.locator('button:has-text("Discard"):visible, button:text-is("Discard"):visible, span:has-text("Discard"):visible').first
                            if discard_btn.is_visible(timeout=2000):
                                discard_btn.click()
                                time.sleep(1)
                        except Exception:
                            pass
                        return
                except Exception:
                    continue

            # Fallback: press Escape
            self.page.keyboard.press("Escape")
            time.sleep(1)
            # Handle discard confirmation
            try:
                discard_btn = self.page.locator('button:has-text("Discard"):visible, button:text-is("Discard"):visible, span:has-text("Discard"):visible').first
                if discard_btn.is_visible(timeout=2000):
                    discard_btn.click()
                    time.sleep(1)
            except Exception:
                pass

        except Exception:
            pass

    def _handle_failure(self, error):
        """Take screenshot and upload to Telegram on failure."""
        try:
            screenshot_path = "screenshot.png"
            self.page.screenshot(path=screenshot_path)
            self.log_fn(f"[INFO] Screenshot saved to {screenshot_path}")
            
            if self.telegram and self.telegram.is_configured:
                caption = f"🚨 LinkedIn Job Application failure alert:\n{str(error)[:150]}"
                self.telegram.send_photo(screenshot_path, caption=caption)
        except Exception as s_err:
            self.log_fn(f"[ERROR] Failed to take/send screenshot: {s_err}")
