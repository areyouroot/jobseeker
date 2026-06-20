import sys
import configparser
from pathlib import Path
from datetime import datetime
from tkinter import messagebox

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE = BASE_DIR / "config.ini"
RESUME_DIR = BASE_DIR / "resume"

class ConfigLoader:
    """Reads and validates config.ini settings for Naukri Auto-Uploader."""

    @staticmethod
    def get_config_file_path() -> Path:
        """Return the configuration file path."""
        return CONFIG_FILE

    @staticmethod
    def get_resume_dir_path() -> Path:
        """Return the resume directory path."""
        return RESUME_DIR

    @classmethod
    def load(cls) -> dict:
        """
        Read and validate config.ini.

        Returns a dictionary with keys:
            - email, password, resume_path, slow_mo, timeout, schedule_times
            - telegram_bot_token, telegram_chat_id (optional, can be empty)
        """
        config_path = cls.get_config_file_path()
        resume_dir_path = cls.get_resume_dir_path()

        if not config_path.exists():
            messagebox.showerror("Config Error", f"Config file not found:\n{config_path}")
            sys.exit(1)

        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")

        try:
            email = config.get("naukri", "email")
            password = config.get("naukri", "password")
            resume_filename = config.get("settings", "resume_filename", fallback="resume.pdf")
            slow_mo = config.getint("settings", "slow_mo", fallback=100)
            timeout = config.getint("settings", "timeout", fallback=30000)
            upload_delay = config.getint("settings", "upload_delay", fallback=10)
            apply_delay = config.getint("settings", "apply_delay", fallback=60)

            times_raw = config.get("schedule", "times", fallback="09:00, 13:00, 16:00")
            schedule_times = [t.strip() for t in times_raw.split(",") if t.strip()]

        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            messagebox.showerror("Config Error", f"Missing required config fields:\n{e}")
            sys.exit(1)

        # Telegram config (optional)
        telegram_bot_token = config.get("telegram", "bot_token", fallback="").strip()
        telegram_chat_id = config.get("telegram", "chat_id", fallback="").strip()

        # LLM config (optional)
        llm_url = ""
        if config.has_section("llm"):
            llm_url = config.get("llm", "url", fallback="").strip()

        if email == "your_email@example.com" or password == "your_password_here":
            messagebox.showerror("Config Error", "Update config.ini with real credentials.")
            sys.exit(1)

        resume_path = resume_dir_path / resume_filename
        if not resume_path.exists():
            messagebox.showerror("Config Error", f"Resume not found:\n{resume_path}")
            sys.exit(1)

        for t in schedule_times:
            try:
                datetime.strptime(t, "%H:%M")
            except ValueError:
                messagebox.showerror("Config Error",
                                     f"Invalid time '{t}' in config.\nUse HH:MM (24-hour).")
                sys.exit(1)

        # Sort times chronologically
        schedule_times.sort()

        return {
            "email": email,
            "password": password,
            "resume_path": str(resume_path),
            "slow_mo": slow_mo,
            "timeout": timeout,
            "upload_delay": upload_delay,
            "apply_delay": apply_delay,
            "schedule_times": schedule_times,
            "telegram_bot_token": telegram_bot_token,
            "telegram_chat_id": telegram_chat_id,
            "llm_url": llm_url,
        }

