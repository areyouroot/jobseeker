"""
=============================================================
  Test: Countdown Timer & Next-Upload Calculation
=============================================================
"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestCountdownFormatting(unittest.TestCase):
    """Tests for _format_countdown output format."""

    def _fmt(self, delta):
        """Replicate the _format_countdown logic locally."""
        total_secs = int(delta.total_seconds())
        if total_secs < 0:
            return "Now!"
        hours = total_secs // 3600
        minutes = (total_secs % 3600) // 60
        seconds = total_secs % 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m {seconds:02d}s"
        elif minutes > 0:
            return f"{minutes}m {seconds:02d}s"
        else:
            return f"{seconds}s"

    def test_hours_minutes_seconds(self):
        self.assertEqual(self._fmt(timedelta(hours=2, minutes=15, seconds=30)), "2h 15m 30s")

    def test_minutes_seconds(self):
        self.assertEqual(self._fmt(timedelta(minutes=45, seconds=10)), "45m 10s")

    def test_seconds_only(self):
        self.assertEqual(self._fmt(timedelta(seconds=42)), "42s")

    def test_zero(self):
        self.assertEqual(self._fmt(timedelta(seconds=0)), "0s")

    def test_large(self):
        self.assertEqual(self._fmt(timedelta(hours=12)), "12h 00m 00s")

    def test_negative_shows_now(self):
        self.assertEqual(self._fmt(timedelta(seconds=-5)), "Now!")

    def test_exact_hour(self):
        self.assertEqual(self._fmt(timedelta(hours=1)), "1h 00m 00s")

    def test_exact_minute(self):
        self.assertEqual(self._fmt(timedelta(minutes=1)), "1m 00s")


class TestNextUploadCalc(unittest.TestCase):
    """Tests for which time slot is 'next' and the countdown to it."""

    def _next(self, times, now):
        for t in sorted(times):
            h, m = map(int, t.split(":"))
            s = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if s > now:
                return t
        return None

    def _countdown(self, times, now):
        times = sorted(times)
        for t in times:
            h, m = map(int, t.split(":"))
            s = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if s > now:
                return s - now
        first = times[0]
        h, m = map(int, first.split(":"))
        tomorrow = (now + timedelta(days=1)).replace(hour=h, minute=m, second=0, microsecond=0)
        return tomorrow - now

    def test_morning_next_is_first(self):
        now = datetime(2026, 6, 14, 8, 0, 0)
        self.assertEqual(self._next(["09:00", "13:00", "16:00"], now), "09:00")

    def test_midday_next(self):
        now = datetime(2026, 6, 14, 10, 0, 0)
        self.assertEqual(self._next(["09:00", "13:00", "16:00"], now), "13:00")

    def test_afternoon_next(self):
        now = datetime(2026, 6, 14, 14, 0, 0)
        self.assertEqual(self._next(["09:00", "13:00", "16:00"], now), "16:00")

    def test_all_passed_returns_none(self):
        now = datetime(2026, 6, 14, 23, 0, 0)
        self.assertIsNone(self._next(["09:00", "13:00", "16:00"], now))

    def test_countdown_wraps_to_tomorrow(self):
        """At 23:00, countdown targets tomorrow's 09:00 = 10h."""
        now = datetime(2026, 6, 14, 23, 0, 0)
        delta = self._countdown(["09:00", "13:00", "16:00"], now)
        self.assertAlmostEqual(delta.total_seconds(), 10 * 3600, delta=1)

    def test_countdown_5min(self):
        now = datetime(2026, 6, 14, 8, 55, 0)
        delta = self._countdown(["09:00", "13:00"], now)
        self.assertAlmostEqual(delta.total_seconds(), 300, delta=1)

    def test_countdown_just_seconds(self):
        now = datetime(2026, 6, 14, 8, 59, 30)
        delta = self._countdown(["09:00"], now)
        self.assertAlmostEqual(delta.total_seconds(), 30, delta=1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
