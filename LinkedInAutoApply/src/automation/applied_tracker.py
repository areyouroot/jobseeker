import json
from pathlib import Path
from datetime import datetime

class AppliedTracker:
    """
    Tracks which LinkedIn jobs have already been applied to, using a local JSON file.
    Prevents duplicate applications across sessions.
    """

    def __init__(self, log_fn=print):
        self.log_fn = log_fn
        self._file_path = Path(__file__).resolve().parent.parent.parent / "applied_jobs.json"
        self._data = self._load()

    def _load(self) -> dict:
        """Load the applied jobs data from disk."""
        if self._file_path.exists():
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                self.log_fn(f"[WARNING] Could not load applied_jobs.json: {e}")
        return {}

    def _save(self):
        """Persist the applied jobs data to disk."""
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_fn(f"[ERROR] Failed to save applied_jobs.json: {e}")

    def is_applied(self, job_id: str) -> bool:
        """Check if a job has already been applied to."""
        return str(job_id) in self._data

    def mark_applied(self, job_id: str, title: str = "", company: str = ""):
        """Mark a job as applied and persist to disk."""
        self._data[str(job_id)] = {
            "title": title,
            "company": company,
            "applied_at": datetime.now().isoformat(),
        }
        self._save()

    def get_count(self) -> int:
        """Return the total number of applied jobs tracked."""
        return len(self._data)
