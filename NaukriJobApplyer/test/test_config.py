"""
=============================================================
  Test: Config Loading & Validation
=============================================================
"""

import configparser
import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import naukri_uploader


class TestConfigLoading(unittest.TestCase):
    """Tests for load_config() — valid configs, missing files, bad values."""

    def setUp(self):
        """Create temp dir with a dummy resume for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.resume_dir = os.path.join(self.test_dir, "resume")
        os.makedirs(self.resume_dir)
        self.resume_path = os.path.join(self.resume_dir, "resume.pdf")
        with open(self.resume_path, "w") as f:
            f.write("dummy")

    def _write_config(self, content):
        path = os.path.join(self.test_dir, "config.ini")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_valid_config_loads(self):
        """A properly filled config.ini loads all fields correctly."""
        cfg_path = self._write_config("""
[naukri]
email = test@example.com
password = mypassword123
[settings]
resume_filename = resume.pdf
slow_mo = 150
timeout = 20000
[schedule]
times = 09:00, 13:00, 16:00
""")
        with patch("naukri_uploader.CONFIG_FILE", Path(cfg_path)), \
             patch("naukri_uploader.RESUME_DIR", Path(self.resume_dir)):
            cfg = naukri_uploader.load_config()

        self.assertEqual(cfg["email"], "test@example.com")
        self.assertEqual(cfg["password"], "mypassword123")
        self.assertEqual(cfg["slow_mo"], 150)
        self.assertEqual(cfg["timeout"], 20000)
        self.assertEqual(cfg["schedule_times"], ["09:00", "13:00", "16:00"])

    def test_missing_config_exits(self):
        """Missing config.ini causes sys.exit."""
        fake = Path(self.test_dir) / "nonexistent.ini"
        with patch("naukri_uploader.CONFIG_FILE", fake):
            with self.assertRaises(SystemExit):
                naukri_uploader.load_config()

    def test_placeholder_credentials_rejected(self):
        """Placeholder email/password are rejected."""
        cfg_path = self._write_config("""
[naukri]
email = your_email@example.com
password = your_password_here
[settings]
resume_filename = resume.pdf
[schedule]
times = 09:00
""")
        with patch("naukri_uploader.CONFIG_FILE", Path(cfg_path)), \
             patch("naukri_uploader.RESUME_DIR", Path(self.resume_dir)):
            with self.assertRaises(SystemExit):
                naukri_uploader.load_config()

    def test_times_are_sorted(self):
        """Schedule times are sorted chronologically."""
        cfg_path = self._write_config("""
[naukri]
email = u@t.com
password = p123
[settings]
resume_filename = resume.pdf
[schedule]
times = 16:00, 09:00, 13:00
""")
        with patch("naukri_uploader.CONFIG_FILE", Path(cfg_path)), \
             patch("naukri_uploader.RESUME_DIR", Path(self.resume_dir)):
            cfg = naukri_uploader.load_config()
        self.assertEqual(cfg["schedule_times"], ["09:00", "13:00", "16:00"])

    def test_invalid_time_format_exits(self):
        """Non HH:MM time format causes sys.exit."""
        cfg_path = self._write_config("""
[naukri]
email = u@t.com
password = p123
[settings]
resume_filename = resume.pdf
[schedule]
times = 9am, 1pm
""")
        with patch("naukri_uploader.CONFIG_FILE", Path(cfg_path)), \
             patch("naukri_uploader.RESUME_DIR", Path(self.resume_dir)):
            with self.assertRaises(SystemExit):
                naukri_uploader.load_config()

    def test_missing_resume_exits(self):
        """Non-existent resume file causes sys.exit."""
        cfg_path = self._write_config("""
[naukri]
email = u@t.com
password = p123
[settings]
resume_filename = nope.pdf
[schedule]
times = 09:00
""")
        with patch("naukri_uploader.CONFIG_FILE", Path(cfg_path)), \
             patch("naukri_uploader.RESUME_DIR", Path(self.resume_dir)):
            with self.assertRaises(SystemExit):
                naukri_uploader.load_config()

    def test_default_settings_applied(self):
        """Missing optional settings use defaults (slow_mo=100, timeout=30000)."""
        cfg_path = self._write_config("""
[naukri]
email = u@t.com
password = p123
[settings]
resume_filename = resume.pdf
[schedule]
times = 10:00
""")
        with patch("naukri_uploader.CONFIG_FILE", Path(cfg_path)), \
             patch("naukri_uploader.RESUME_DIR", Path(self.resume_dir)):
            cfg = naukri_uploader.load_config()
        self.assertEqual(cfg["slow_mo"], 100)
        self.assertEqual(cfg["timeout"], 30000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
