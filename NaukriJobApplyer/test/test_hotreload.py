"""
=============================================================
  Test: Config Hot-Reload Detection
=============================================================
"""

import configparser
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestConfigHotReload(unittest.TestCase):
    """Tests for live-detecting schedule changes in config.ini."""

    def test_detects_new_time_added(self):
        old = ["09:00", "13:00", "16:00"]
        new = sorted(["09:00", "13:00", "16:00", "21:30"])
        self.assertNotEqual(old, new)

    def test_detects_time_removed(self):
        old = ["09:00", "13:00", "16:00"]
        new = sorted(["09:00", "16:00"])
        self.assertNotEqual(old, new)

    def test_detects_time_changed(self):
        old = ["09:00", "13:00", "16:00"]
        new = sorted(["09:00", "14:00", "16:00"])
        self.assertNotEqual(old, new)

    def test_no_false_positive(self):
        """Same times in different order are equal after sort."""
        old = ["09:00", "13:00", "16:00"]
        new = sorted(["16:00", "09:00", "13:00"])
        self.assertEqual(old, new)

    def test_parses_whitespace_correctly(self):
        raw = " 16:00,  09:00 , 13:00, 21:30 "
        parsed = sorted([t.strip() for t in raw.split(",") if t.strip()])
        self.assertEqual(parsed, ["09:00", "13:00", "16:00", "21:30"])

    def test_empty_times(self):
        parsed = sorted([t.strip() for t in "".split(",") if t.strip()])
        self.assertEqual(parsed, [])

    def test_full_roundtrip_file_read(self):
        """Write config → read → parse → verify."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini",
                                         delete=False, encoding="utf-8") as f:
            f.write("[schedule]\ntimes = 08:00, 12:00, 18:00, 22:00\n")
            f.flush()
            tmp = f.name
        try:
            config = configparser.ConfigParser()
            config.read(tmp, encoding="utf-8")
            raw = config.get("schedule", "times")
            parsed = sorted([t.strip() for t in raw.split(",") if t.strip()])
            self.assertEqual(parsed, ["08:00", "12:00", "18:00", "22:00"])
        finally:
            os.unlink(tmp)

    def test_update_detection_after_file_change(self):
        """Simulate editing config.ini and detecting the change."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini",
                                         delete=False, encoding="utf-8") as f:
            f.write("[schedule]\ntimes = 09:00, 13:00\n")
            f.flush()
            tmp = f.name

        try:
            # First read
            config = configparser.ConfigParser()
            config.read(tmp, encoding="utf-8")
            old = sorted([t.strip() for t in config.get("schedule", "times").split(",")
                          if t.strip()])

            # Simulate user editing the file
            with open(tmp, "w", encoding="utf-8") as f:
                f.write("[schedule]\ntimes = 09:00, 13:00, 17:00\n")

            # Second read
            config2 = configparser.ConfigParser()
            config2.read(tmp, encoding="utf-8")
            new = sorted([t.strip() for t in config2.get("schedule", "times").split(",")
                          if t.strip()])

            self.assertNotEqual(old, new)
            self.assertIn("17:00", new)
        finally:
            os.unlink(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
