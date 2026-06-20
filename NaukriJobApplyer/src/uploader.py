import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

class ResumeUploader:
    """Handles automated resume uploading on the Naukri.com profile page."""

    def __init__(self, page, resume_path: str, timeout: int, log_fn=print):
        self.page = page
        self.resume_path = resume_path
        self.timeout = timeout
        self.log_fn = log_fn

    def upload(self) -> bool:
        """Upload the resume on the profile page. Returns True on success."""
        self.log_fn("[INFO] Navigating to profile page...")
        self.page.goto(NAUKRI_PROFILE_URL, wait_until="domcontentloaded", timeout=self.timeout)
        time.sleep(3)

        self.log_fn("[INFO] Looking for resume upload input...")
        file_input = self.page.locator('input[type="file"]').first

        try:
            self.log_fn("[INFO] Uploading resume...")
            file_input.set_input_files(self.resume_path)
            time.sleep(5)
            self.log_fn("[SUCCESS] Resume uploaded successfully!")
            return True

        except PlaywrightTimeoutError:
            self.log_fn("[WARNING] Direct upload failed, trying fallback...")
            try:
                update_btn = self.page.locator(
                    'text="Update resume",'
                    'text="Upload Resume",'
                    '[class*="resume"] >> text="Update"'
                ).first
                update_btn.wait_for(state="visible", timeout=self.timeout)
                update_btn.click()
                time.sleep(2)
                file_input = self.page.locator('input[type="file"]').first
                file_input.set_input_files(self.resume_path)
                time.sleep(5)
                self.log_fn("[SUCCESS] Resume uploaded (fallback)!")
                return True
            except Exception as e:
                self.log_fn(f"[ERROR] Upload failed: {e}")
                return False
