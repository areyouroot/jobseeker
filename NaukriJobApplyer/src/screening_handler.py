import time

class ScreeningHandler:
    """Detects and handles recruiter pre-screening question modals."""

    def __init__(self, page, telegram_bot, timeout: int, log_fn=print):
        self.page = page
        self.telegram = telegram_bot
        self.timeout = timeout
        self.log_fn = log_fn

    def handle_screening_questions(self):
        """
        Check if a modal appeared with pre-screening questions.
        If so, relay each question via Telegram and fill in the user's reply.
        """
        # Wait briefly for a modal / overlay to appear
        time.sleep(2)

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

        if not modal:
            self.log_fn("[INFO] No screening questions detected.")
            return

        self.log_fn("[INFO] 📝 Screening question modal detected!")

        # Find question labels + input fields inside the modal
        questions = modal.locator(
            'label, [class*="question"], [class*="Question"], [class*="label"], p:near(input), p:near(textarea)'
        )
        inputs = modal.locator(
            'input[type="text"], input[type="number"], textarea, select, input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"])'
        )

        q_count = questions.count()
        i_count = inputs.count()
        pairs = min(q_count, i_count)

        if pairs == 0:
            # Maybe the modal just has a single text area
            try:
                solo_input = modal.locator('textarea, input[type="text"]').first
                if solo_input.is_visible(timeout=1500):
                    modal_text = modal.inner_text(timeout=2000)
                    question_text = modal_text.replace("\n", " ").strip()[:300]
                    self.log_fn(f"[INFO] Question: {question_text}")

                    if self.telegram.is_configured:
                        answer = self.telegram.ask_question(question_text)
                        if answer:
                            solo_input.fill(answer)
                            self.log_fn(f"[INFO] Filled answer: {answer}")
                    else:
                        self.log_fn("[WARNING] Telegram not configured — cannot answer question.")
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
                        answer = self.telegram.ask_question(q_label)
                        if answer:
                            tag = inp.evaluate("el => el.tagName.toLowerCase()")
                            if tag == "select":
                                inp.select_option(label=answer)
                            else:
                                inp.fill(answer)
                            self.log_fn(f"[INFO] Filled answer for Q{idx+1}: {answer}")
                        else:
                            self.log_fn(f"[WARNING] No answer received for Q{idx+1}, skipping.")
                    else:
                        self.log_fn("[WARNING] Telegram not configured — cannot answer.")
                except Exception as qe:
                    self.log_fn(f"[WARNING] Error processing question {idx+1}: {qe}")

        # Try to submit the answers
        submit_selectors = [
            'button:has-text("Submit")',
            'button:has-text("Apply")',
            'button:has-text("Send")',
            'button[type="submit"]',
            'input[type="submit"]',
        ]
        for sel in submit_selectors:
            try:
                submit_btn = modal.locator(sel).first
                if submit_btn.is_visible(timeout=1500):
                    submit_btn.click()
                    self.log_fn("[SUCCESS] Submitted screening answers.")
                    time.sleep(2)
                    return
            except Exception:
                continue

        self.log_fn("[WARNING] Could not find a submit button for screening questions.")
