import time
from src.browser_controller import NaukriBrowser
from src.session import NaukriSession
from src.uploader import ResumeUploader
from src.telegram_bot import TelegramBot
from src.nvite_handler import NViteHandler

class UploadOrchestrator:
    """Orchestrates one complete upload and check cycle."""

    def __init__(self, cfg: dict, log_fn=print, status_fn=None):
        self.cfg = cfg
        self.log_fn = log_fn
        self.status_fn = status_fn

    def run_once(self):
        """Launch browser -> login -> upload -> check NVites -> close -> send summary."""
        if self.status_fn:
            self.status_fn("uploading")

        self.log_fn("[TRIGGER] Starting upload cycle...")

        telegram_bot = TelegramBot(
            self.cfg.get("telegram_bot_token", ""),
            self.cfg.get("telegram_chat_id", ""),
            self.log_fn,
        )

        browser_controller = NaukriBrowser(
            slow_mo=self.cfg["slow_mo"],
            timeout=self.cfg["timeout"],
            log_fn=self.log_fn,
        )

        upload_status = "Skipped"
        nvites_count = 0
        applied_details = {}
        total_jobs_applied = 0
        error_occurred = False
        error_message = ""

        try:
            page = browser_controller.launch()

            session = NaukriSession(
                page=page,
                email=self.cfg["email"],
                password=self.cfg["password"],
                timeout=self.cfg["timeout"],
                log_fn=self.log_fn,
            )

            login_success = session.login()
            if login_success:
                uploader = ResumeUploader(
                    page=page,
                    resume_path=self.cfg["resume_path"],
                    timeout=self.cfg["timeout"],
                    log_fn=self.log_fn,
                )
                upload_success = uploader.upload()
                upload_status = "Success" if upload_success else "Failed"

                # Sleep configurable upload_delay after upload completes
                upload_delay = self.cfg.get("upload_delay", 10)
                self.log_fn(f"[INFO] Sleeping for {upload_delay} seconds (upload delay)...")
                time.sleep(upload_delay)

                # After uploading, check for new NVites
                try:
                    nvite_handler = NViteHandler(
                        page=page,
                        telegram_bot=telegram_bot,
                        timeout=self.cfg["timeout"],
                        log_fn=self.log_fn,
                    )
                    nvites_count = nvite_handler.check_and_accept_nvites()
                except Exception as nvite_err:
                    self.log_fn(f"[WARNING] NVite check failed: {nvite_err}")

                # If llm_url is configured, run job search & application flow
                llm_url = self.cfg.get("llm_url", "")
                if llm_url:
                    from src.llm_client import LLMClient
                    from src.automation.job_applier import JobApplier

                    llm_client = LLMClient(llm_url=llm_url, log_fn=self.log_fn)
                    keywords = llm_client.get_keywords(self.cfg["resume_path"])
                    self.log_fn(f"[INFO] Extracted keywords for job search: {keywords}")

                    if keywords:
                        job_applier = JobApplier(
                            page=page,
                            telegram_bot=telegram_bot,
                            apply_delay=self.cfg.get("apply_delay", 60),
                            timeout=self.cfg["timeout"],
                            log_fn=self.log_fn,
                        )
                        job_applier.apply_for_jobs(keywords)
                        applied_details = job_applier.applied_details
                        total_jobs_applied = job_applier.total_applied
            else:
                upload_status = "Skipped (Login Failed)"
                self.log_fn("[ERROR] Login failed — skipping upload.")

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
                
                # Format jobs details
                job_summary_lines = []
                if applied_details:
                    for kw, count in applied_details.items():
                        job_summary_lines.append(f"• <code>{kw}</code>: {count} applied")
                else:
                    llm_url = self.cfg.get("llm_url", "")
                    if llm_url:
                        job_summary_lines.append("• No jobs successfully applied")
                    else:
                        job_summary_lines.append("• Not run (LLM not configured)")

                job_details_str = "\n".join(job_summary_lines)

                summary_text = (
                    "📋 <b>Naukri Cycle Run Summary</b>\n\n"
                    f"👤 <b>Account:</b> {self.cfg['email']}\n"
                    f"📄 <b>Resume Upload:</b> {upload_status}\n"
                    f"🔔 <b>Invites (NVites) Accepted:</b> {nvites_count}\n\n"
                    f"💼 <b>Jobs Applied by Keywords:</b>\n{job_details_str}\n\n"
                    f"📊 <b>Total Jobs Applied:</b> {total_jobs_applied}/15"
                )

                if error_occurred:
                    summary_text += f"\n\n⚠️ <b>Warning:</b> Cycle ended with error:\n<code>{error_message[:200]}</code>"

                telegram_bot.send_message(summary_text)

        if self.status_fn:
            self.status_fn("idle")
