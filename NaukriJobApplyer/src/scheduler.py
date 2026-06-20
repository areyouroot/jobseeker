import threading
from datetime import datetime
from src.orchestrator import UploadOrchestrator

class UploadScheduler:
    """
    Background scheduler — checks time every 10 seconds, fires uploads
    at configured times, resets daily at midnight.
    """

    def __init__(self, cfg, log_fn=print, status_fn=None):
        self.cfg = cfg
        self.log_fn = log_fn
        self.status_fn = status_fn
        self._stop_event = threading.Event()
        self._thread = None
        self._fired_today = set()
        self._today = datetime.now().date()
        self.upload_count = 0
        self.last_upload_time = None

    def start(self):
        """Start the background scheduler thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._fired_today.clear()
        self._today = datetime.now().date()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.log_fn("[INFO] Scheduler started.")
        self.log_fn(f"[INFO] Scheduled times: {', '.join(self.cfg['schedule_times'])}")

    def stop(self):
        """Stop the background scheduler thread."""
        self._stop_event.set()
        self.log_fn("[INFO] Scheduler stopped.")

    def is_running(self):
        """Return True if the scheduler thread is running."""
        return self._thread is not None and self._thread.is_alive()

    def _run_loop(self):
        """The main scheduler loop running in a background thread."""
        self.log_fn("[INFO] Scheduler loop active — checking every 10 seconds.")
        while not self._stop_event.is_set():
            now = datetime.now()

            # Reset fired slots at midnight
            if now.date() != self._today:
                self._fired_today.clear()
                self._today = now.date()
                self.log_fn("[INFO] New day — schedule reset.")

            # Check each scheduled time — match if we're within a 2-minute window
            # so we never miss a slot even if polling is slightly off
            for t in self.cfg["schedule_times"]:
                if t in self._fired_today:
                    continue
                h, m = map(int, t.split(":"))
                scheduled = now.replace(hour=h, minute=m, second=0, microsecond=0)
                diff = (now - scheduled).total_seconds()
                # Fire if we are within 0 to 120 seconds past the scheduled time
                if 0 <= diff < 120:
                    self._fired_today.add(t)
                    self.log_fn(f"\n[TRIGGER] ⏰ Scheduled upload at {t}!")
                    try:
                        orchestrator = UploadOrchestrator(self.cfg, self.log_fn, self.status_fn)
                        orchestrator.run_once()
                        self.upload_count += 1
                        self.last_upload_time = datetime.now()
                    except Exception as e:
                        self.log_fn(f"[ERROR] Upload failed: {e}")

            # Poll every 10 seconds for more responsive timing
            self._stop_event.wait(timeout=10)
