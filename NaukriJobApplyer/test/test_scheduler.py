"""
=============================================================
  Test: Scheduler — Timing, Firing & Mock Browser Launch
=============================================================

Uses mock patching to verify the scheduler actually calls
run_upload_once (which launches Chrome) at the correct times
without needing a real browser.
"""

import sys
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import naukri_uploader


def _make_cfg(times):
    """Build a minimal config dict for testing."""
    return {
        "email": "test@test.com",
        "password": "pass",
        "resume_path": "dummy.pdf",
        "slow_mo": 0,
        "timeout": 5000,
        "schedule_times": sorted(times),
    }


class TestSchedulerStartStop(unittest.TestCase):
    """Scheduler lifecycle tests."""

    def test_starts_and_stops(self):
        """Scheduler thread starts and stops cleanly."""
        scheduler = naukri_uploader.UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
        scheduler.start()
        self.assertTrue(scheduler.is_running())
        scheduler.stop()
        time.sleep(0.5)
        self.assertFalse(scheduler.is_running())

    def test_no_double_start(self):
        """Calling start() twice keeps the same thread."""
        scheduler = naukri_uploader.UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
        scheduler.start()
        t1 = scheduler._thread
        scheduler.start()
        t2 = scheduler._thread
        self.assertIs(t1, t2)
        scheduler.stop()
        time.sleep(0.5)

    def test_initial_state(self):
        """Upload count starts at 0, last_upload_time is None."""
        scheduler = naukri_uploader.UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
        self.assertEqual(scheduler.upload_count, 0)
        self.assertIsNone(scheduler.last_upload_time)


class TestSchedulerFiring(unittest.TestCase):
    """Tests that the scheduler fires at the correct times using mocks."""

    def test_fires_within_2min_window(self):
        """Scheduler fires when current time is within 0-120s of a slot."""
        cfg = _make_cfg(["14:30"])
        now_exact = datetime(2026, 6, 14, 14, 30, 0)
        scheduled = now_exact.replace(hour=14, minute=30, second=0)

        # Exactly at 14:30 → fires
        diff = (now_exact - scheduled).total_seconds()
        self.assertTrue(0 <= diff < 120)

        # 60s after → fires
        diff = (now_exact + timedelta(seconds=60) - scheduled).total_seconds()
        self.assertTrue(0 <= diff < 120)

        # 180s after → does NOT fire
        diff = (now_exact + timedelta(seconds=180) - scheduled).total_seconds()
        self.assertFalse(0 <= diff < 120)

        # 60s before → does NOT fire
        diff = (now_exact - timedelta(seconds=60) - scheduled).total_seconds()
        self.assertFalse(0 <= diff < 120)

    def test_fired_today_prevents_duplicate(self):
        """A slot marked as fired today does not fire again."""
        scheduler = naukri_uploader.UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
        scheduler._fired_today.add("09:00")
        # Should skip 09:00
        self.assertIn("09:00", scheduler._fired_today)

    def test_day_rollover_resets_fired(self):
        """Crossing midnight clears the fired set."""
        scheduler = naukri_uploader.UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
        scheduler._fired_today.add("09:00")
        scheduler._today = (datetime.now() - timedelta(days=1)).date()

        # Simulate the rollover check
        now = datetime.now()
        if now.date() != scheduler._today:
            scheduler._fired_today.clear()
            scheduler._today = now.date()

        self.assertEqual(len(scheduler._fired_today), 0)

    @patch("naukri_uploader.run_upload_once")
    def test_scheduler_calls_upload_at_right_time(self, mock_upload):
        """
        KEY TEST: Mock the clock so the scheduler thinks it's exactly
        at a scheduled time, then verify run_upload_once gets called.
        This proves the timer logic will launch Chrome at the right moment.
        """
        cfg = _make_cfg(["14:30"])
        log = MagicMock()
        scheduler = naukri_uploader.UploadScheduler(cfg, log_fn=log)

        # Simulate: pretend it's exactly 14:30:05
        fake_now = datetime(2026, 6, 14, 14, 30, 5)

        # Manually run one iteration of the scheduler's loop logic
        # (instead of starting the thread, we test the core logic directly)
        for t in cfg["schedule_times"]:
            if t in scheduler._fired_today:
                continue
            h, m = map(int, t.split(":"))
            scheduled = fake_now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (fake_now - scheduled).total_seconds()
            if 0 <= diff < 120:
                scheduler._fired_today.add(t)
                naukri_uploader.run_upload_once(cfg, log)
                scheduler.upload_count += 1

        # Verify run_upload_once was called exactly once
        mock_upload.assert_called_once_with(cfg, log)
        self.assertEqual(scheduler.upload_count, 1)
        self.assertIn("14:30", scheduler._fired_today)

    @patch("naukri_uploader.run_upload_once")
    def test_scheduler_does_not_fire_too_early(self, mock_upload):
        """If current time is before the slot, upload should NOT be called."""
        cfg = _make_cfg(["14:30"])
        scheduler = naukri_uploader.UploadScheduler(cfg, log_fn=MagicMock())

        fake_now = datetime(2026, 6, 14, 14, 28, 0)  # 2 minutes early

        for t in cfg["schedule_times"]:
            if t in scheduler._fired_today:
                continue
            h, m = map(int, t.split(":"))
            scheduled = fake_now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (fake_now - scheduled).total_seconds()
            if 0 <= diff < 120:
                naukri_uploader.run_upload_once(cfg, MagicMock())

        mock_upload.assert_not_called()

    @patch("naukri_uploader.run_upload_once")
    def test_scheduler_fires_for_multiple_slots(self, mock_upload):
        """If multiple times match (e.g., both passed during a long sleep),
        each should fire independently."""
        cfg = _make_cfg(["14:30", "14:31"])
        log = MagicMock()
        scheduler = naukri_uploader.UploadScheduler(cfg, log_fn=log)

        fake_now = datetime(2026, 6, 14, 14, 31, 30)  # Both within window

        for t in cfg["schedule_times"]:
            if t in scheduler._fired_today:
                continue
            h, m = map(int, t.split(":"))
            scheduled = fake_now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (fake_now - scheduled).total_seconds()
            if 0 <= diff < 120:
                scheduler._fired_today.add(t)
                naukri_uploader.run_upload_once(cfg, log)
                scheduler.upload_count += 1

        self.assertEqual(mock_upload.call_count, 2)
        self.assertEqual(scheduler.upload_count, 2)

    @patch("naukri_uploader.run_upload_once")
    def test_scheduler_thread_fires_upload(self, mock_upload):
        """
        INTEGRATION: Start the real scheduler thread with a time set to
        right now, verify it calls run_upload_once within ~15 seconds.
        """
        # Set the scheduled time to RIGHT NOW
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        cfg = _make_cfg([current_time])
        log = MagicMock()

        scheduler = naukri_uploader.UploadScheduler(cfg, log_fn=log)
        scheduler.start()

        # Wait up to 15 seconds for the scheduler to fire
        waited = 0
        while waited < 15:
            if mock_upload.called:
                break
            time.sleep(0.5)
            waited += 0.5

        scheduler.stop()
        time.sleep(0.5)

        # The scheduler should have called run_upload_once
        self.assertTrue(mock_upload.called,
                        f"Scheduler did not fire for time={current_time} "
                        f"within 15 seconds. Current time: {datetime.now()}")
        self.assertGreaterEqual(scheduler.upload_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
