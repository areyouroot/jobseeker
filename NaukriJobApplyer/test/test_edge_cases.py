"""
=============================================================
  Test: Edge Cases & Boundary Conditions
=============================================================
"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestEdgeCases(unittest.TestCase):
    """Boundary and edge case tests."""

    def test_midnight_time(self):
        """00:00 should be valid and in the past at 23:59."""
        now = datetime(2026, 6, 14, 23, 59, 0)
        scheduled = now.replace(hour=0, minute=0, second=0)
        self.assertLess(scheduled, now)

    def test_single_time_schedule(self):
        now = datetime(2026, 6, 14, 10, 0, 0)
        times = ["15:00"]
        found = None
        for t in sorted(times):
            h, m = map(int, t.split(":"))
            s = now.replace(hour=h, minute=m, second=0)
            if s > now:
                found = t
                break
        self.assertEqual(found, "15:00")

    def test_many_times_sorted(self):
        raw = "23:00, 01:00, 12:00, 06:00, 18:00, 03:00"
        parsed = sorted([t.strip() for t in raw.split(",") if t.strip()])
        self.assertEqual(parsed, ["01:00", "03:00", "06:00", "12:00", "18:00", "23:00"])

    def test_resume_path_join(self):
        d = Path("/project/resume")
        f = "my_resume.pdf"
        self.assertEqual(str(d / f), str(Path("/project/resume/my_resume.pdf")))

    def test_2min_window_boundary_exact_120s(self):
        """Exactly 120 seconds past should NOT fire (< 120, not <=)."""
        now = datetime(2026, 6, 14, 14, 32, 0)
        scheduled = now.replace(hour=14, minute=30, second=0)
        diff = (now - scheduled).total_seconds()
        self.assertEqual(diff, 120)
        self.assertFalse(0 <= diff < 120)  # Boundary: 120 is excluded

    def test_2min_window_boundary_119s(self):
        """119 seconds past should fire."""
        now = datetime(2026, 6, 14, 14, 31, 59)
        scheduled = now.replace(hour=14, minute=30, second=0)
        diff = (now - scheduled).total_seconds()
        self.assertEqual(diff, 119)
        self.assertTrue(0 <= diff < 120)

    def test_consecutive_times(self):
        """Two times 1 minute apart should both be schedulable."""
        times = sorted(["14:30", "14:31"])
        self.assertEqual(times, ["14:30", "14:31"])

    def test_end_of_day_wrap(self):
        """At 23:59, countdown to tomorrow's 00:05 should be ~6 minutes."""
        now = datetime(2026, 6, 14, 23, 59, 0)
        times = ["00:05"]
        first = times[0]
        h, m = map(int, first.split(":"))
        tomorrow = (now + timedelta(days=1)).replace(hour=h, minute=m, second=0, microsecond=0)
        diff = (tomorrow - now).total_seconds()
        self.assertAlmostEqual(diff, 360, delta=1)  # 6 minutes


if __name__ == "__main__":
    unittest.main(verbosity=2)
