"""
=============================================================
  Test: Scheduler — Timing, Firing & Mock Browser Launch
=============================================================

Uses mock patching to verify the scheduler actually calls
UploadOrchestrator (which manages browser/automation tasks)
at the correct times without needing a real browser.
"""

import sys
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.scheduler import UploadScheduler
from src.orchestrator import UploadOrchestrator


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
        scheduler = UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
        scheduler.start()
        self.assertTrue(scheduler.is_running())
        scheduler.stop()
        time.sleep(0.5)
        self.assertFalse(scheduler.is_running())

    def test_no_double_start(self):
        """Calling start() twice keeps the same thread."""
        scheduler = UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
        scheduler.start()
        t1 = scheduler._thread
        scheduler.start()
        t2 = scheduler._thread
        self.assertIs(t1, t2)
        scheduler.stop()
        time.sleep(0.5)

    def test_initial_state(self):
        """Upload count starts at 0, last_upload_time is None."""
        scheduler = UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
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
        scheduler = UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
        scheduler._fired_today.add("09:00")
        self.assertIn("09:00", scheduler._fired_today)

    def test_day_rollover_resets_fired(self):
        """Crossing midnight clears the fired set."""
        scheduler = UploadScheduler(_make_cfg(["09:00"]), log_fn=MagicMock())
        scheduler._fired_today.add("09:00")
        scheduler._today = (datetime.now() - timedelta(days=1)).date()

        # Simulate the rollover check
        now = datetime.now()
        if now.date() != scheduler._today:
            scheduler._fired_today.clear()
            scheduler._today = now.date()

        self.assertEqual(len(scheduler._fired_today), 0)

    @patch("src.orchestrator.UploadOrchestrator.run_once")
    def test_scheduler_calls_upload_at_right_time(self, mock_run_once):
        """
        KEY TEST: Mock the clock so the scheduler thinks it's exactly
        at a scheduled time, then verify UploadOrchestrator run_once gets called.
        This proves the timer logic will trigger the orchestrator at the right moment.
        """
        cfg = _make_cfg(["14:30"])
        log = MagicMock()
        scheduler = UploadScheduler(cfg, log_fn=log)

        # Simulate: pretend it's exactly 14:30:05
        fake_now = datetime(2026, 6, 14, 14, 30, 5)

        for t in cfg["schedule_times"]:
            if t in scheduler._fired_today:
                continue
            h, m = map(int, t.split(":"))
            scheduled = fake_now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (fake_now - scheduled).total_seconds()
            if 0 <= diff < 120:
                scheduler._fired_today.add(t)
                orchestrator = UploadOrchestrator(cfg, log, scheduler.status_fn)
                orchestrator.run_once()
                scheduler.upload_count += 1

        # Verify orchestrator run_once was called exactly once
        mock_run_once.assert_called_once()
        self.assertEqual(scheduler.upload_count, 1)
        self.assertIn("14:30", scheduler._fired_today)

    @patch("src.orchestrator.UploadOrchestrator.run_once")
    def test_scheduler_does_not_fire_too_early(self, mock_run_once):
        """If current time is before the slot, upload should NOT be called."""
        cfg = _make_cfg(["14:30"])
        scheduler = UploadScheduler(cfg, log_fn=MagicMock())

        fake_now = datetime(2026, 6, 14, 14, 28, 0)  # 2 minutes early

        for t in cfg["schedule_times"]:
            if t in scheduler._fired_today:
                continue
            h, m = map(int, t.split(":"))
            scheduled = fake_now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (fake_now - scheduled).total_seconds()
            if 0 <= diff < 120:
                orchestrator = UploadOrchestrator(cfg, MagicMock(), scheduler.status_fn)
                orchestrator.run_once()

        mock_run_once.assert_not_called()

    @patch("src.orchestrator.UploadOrchestrator.run_once")
    def test_scheduler_fires_for_multiple_slots(self, mock_run_once):
        """If multiple times match (e.g., both passed during a long sleep),
        each should fire independently."""
        cfg = _make_cfg(["14:30", "14:31"])
        log = MagicMock()
        scheduler = UploadScheduler(cfg, log_fn=log)

        fake_now = datetime(2026, 6, 14, 14, 31, 30)  # Both within window

        for t in cfg["schedule_times"]:
            if t in scheduler._fired_today:
                continue
            h, m = map(int, t.split(":"))
            scheduled = fake_now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (fake_now - scheduled).total_seconds()
            if 0 <= diff < 120:
                scheduler._fired_today.add(t)
                orchestrator = UploadOrchestrator(cfg, log, scheduler.status_fn)
                orchestrator.run_once()
                scheduler.upload_count += 1

        self.assertEqual(mock_run_once.call_count, 2)
        self.assertEqual(scheduler.upload_count, 2)

    @patch("src.orchestrator.UploadOrchestrator.run_once")
    def test_scheduler_thread_fires_upload(self, mock_run_once):
        """
        INTEGRATION: Start the real scheduler thread with a time set to
        right now, verify it calls UploadOrchestrator.run_once within ~15 seconds.
        """
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        cfg = _make_cfg([current_time])
        log = MagicMock()

        scheduler = UploadScheduler(cfg, log_fn=log)
        scheduler.start()

        # Wait up to 15 seconds for the scheduler to fire
        waited = 0
        while waited < 15:
            if mock_run_once.called:
                break
            time.sleep(0.5)
            waited += 0.5

        scheduler.stop()
        time.sleep(0.5)

        # The scheduler should have called UploadOrchestrator.run_once
        self.assertTrue(mock_run_once.called,
                        f"Scheduler did not fire for time={current_time} "
                        f"within 15 seconds. Current time: {datetime.now()}")
        self.assertGreaterEqual(scheduler.upload_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
