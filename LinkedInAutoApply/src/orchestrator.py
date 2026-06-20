import time
from src.browser_controller import LinkedInBrowser
from src.session import LinkedInSession
from src.telegram_bot import TelegramBot

class ApplyOrchestrator:
    """Orchestrates one complete LinkedIn Easy Apply cycle."""

    def __init__(self, cfg: dict, log_fn=print, status_fn=None):
        self.cfg = cfg
        self.log_fn = log_fn
        self.status_fn = status_fn

    def run_once(self):
        """Launch browser -> login -> search jobs -> apply -> close -> send summary."""
        if self.status_fn:
            self.status_fn("applying")

        self.log_fn("[TRIGGER] Starting LinkedIn Easy Apply cycle...")

        telegram_bot = TelegramBot(
            self.cfg.get("telegram_bot_token", ""),
            self.cfg.get("telegram_chat_id", ""),
            self.log_fn,
        )

        browser_controller = LinkedInBrowser(
            slow_mo=self.cfg["slow_mo"],
            timeout=self.cfg["timeout"],
            log_fn=self.log_fn,
        )

        applied_details = {}
        total_jobs_applied = 0
        error_occurred = False
        error_message = ""

        try:
            page = browser_controller.launch()

            session = LinkedInSession(
                page=page,
                email=self.cfg["email"],
                password=self.cfg["password"],
                timeout=self.cfg["timeout"],
                telegram_bot=telegram_bot,
                browser_controller=browser_controller,
                log_fn=self.log_fn,
            )

            login_success = session.login()
            if login_success:
                # Get keywords from LLM or use fallback
                llm_url = self.cfg.get("llm_url", "")
                keywords = ["C# .NET Developer"]

                if llm_url:
                    from src.llm_client import LLMClient
                    llm_client = LLMClient(llm_url=llm_url, log_fn=self.log_fn)
                    keywords = llm_client.get_keywords(self.cfg["resume_path"])
                    self.log_fn(f"[INFO] Extracted keywords for job search: {keywords}")

                # Run job search & application flow
                from src.automation.job_applier import JobApplier

                job_applier = JobApplier(
                    page=page,
                    telegram_bot=telegram_bot,
                    apply_delay=self.cfg.get("apply_delay", 60),
                    timeout=self.cfg["timeout"],
                    max_applications=self.cfg.get("max_applications", 25),
                    resume_path=self.cfg.get("resume_path", ""),
                    filters=self.cfg.get("filters", {}),
                    log_fn=self.log_fn,
                )
                job_applier.apply_for_jobs(keywords)
                applied_details = job_applier.applied_details
                total_jobs_applied = job_applier.total_applied
            else:
                self.log_fn("[ERROR] Login failed — cannot proceed.")

        except Exception as e:
            error_occurred = True
            error_message = str(e)
            self.log_fn(f"[ERROR] {e}")
            try:
                screenshot_path = "screenshot.png"
                if 'page' in locals() and not page.is_closed():
                    page.screenshot(path=screenshot_path)
                    self.log_fn(f"[INFO] Saved failure screenshot to {screenshot_path}")
                    if telegram_bot.is_configured:
                        telegram_bot.send_photo(screenshot_path, caption=f"🚨 Flow failure alert:\n{str(e)[:150]}")
            except Exception as s_err:
                self.log_fn(f"[ERROR] Failed to save/send failure screenshot: {s_err}")
        finally:
            time.sleep(2)
            browser_controller.close()

            # Send summary report after browser is closed
            if telegram_bot.is_configured:
                self.log_fn("[INFO] Sending workflow run summary to Telegram...")
                
                max_apps = self.cfg.get("max_applications", 25)

                # Format jobs details
                job_summary_lines = []
                if applied_details:
                    for kw, count in applied_details.items():
                        job_summary_lines.append(f"• <code>{kw}</code>: {count} applied")
                else:
                    job_summary_lines.append("• No jobs successfully applied")

                job_details_str = "\n".join(job_summary_lines)

                summary_text = (
                    "📋 <b>LinkedIn Easy Apply Cycle Summary</b>\n\n"
                    f"👤 <b>Account:</b> {self.cfg['email']}\n\n"
                    f"💼 <b>Jobs Applied by Keywords:</b>\n{job_details_str}\n\n"
                    f"📊 <b>Total Jobs Applied:</b> {total_jobs_applied}/{max_apps}"
                )

                if error_occurred:
                    summary_text += f"\n\n⚠️ <b>Warning:</b> Cycle ended with error:\n<code>{error_message[:200]}</code>"

                telegram_bot.send_message(summary_text)

        if self.status_fn:
            self.status_fn("idle")
