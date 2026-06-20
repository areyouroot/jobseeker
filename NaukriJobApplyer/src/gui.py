import tkinter as tk
import threading
import configparser
from datetime import datetime, timedelta
from pathlib import Path

from src.colors import Colors
from src.widgets import HoverButton
from src.scheduler import UploadScheduler
from src.orchestrator import UploadOrchestrator
from src.config import CONFIG_FILE

class NaukriUploaderApp:
    """
    Desktop GUI with interactive buttons, live log, status dashboard,
    and hover/active visual feedback.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.scheduler = UploadScheduler(cfg, log_fn=self.log, status_fn=self._set_activity)
        self._current_activity = "idle"  # idle | running | uploading

        # Main window
        self.root = tk.Tk()
        self.root.title("Naukri Resume Auto-Uploader")
        self.root.configure(bg=Colors.BG_DARK)
        self.root.geometry("820x650")
        self.root.minsize(700, 550)
        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)

        # Try to set the window icon (suppress errors if not available)
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        self._build_ui()
        self._update_clock()
        self._update_status_indicator()
        self._start_config_watcher()

    def _build_ui(self):
        """Build all UI components."""
        # Title bar
        title_bar = tk.Frame(self.root, bg=Colors.BG_CARD, pady=14,
                             highlightbackground=Colors.BORDER, highlightthickness=1)
        title_bar.pack(fill=tk.X)

        tk.Label(
            title_bar, text="⚡ Naukri Resume Auto-Uploader",
            font=("Segoe UI", 20, "bold"), fg=Colors.ACCENT_CYAN, bg=Colors.BG_CARD,
        ).pack(side=tk.LEFT, padx=20)

        # Live clock on the right side of title bar
        self.clock_label = tk.Label(
            title_bar, text="", font=("Segoe UI", 11),
            fg=Colors.FG_SECONDARY, bg=Colors.BG_CARD,
        )
        self.clock_label.pack(side=tk.RIGHT, padx=20)

        # Status Dashboard
        dashboard = tk.Frame(self.root, bg=Colors.BG_DARK, pady=8)
        dashboard.pack(fill=tk.X, padx=16)

        # Row of status cards
        cards_frame = tk.Frame(dashboard, bg=Colors.BG_DARK)
        cards_frame.pack(fill=tk.X)
        cards_frame.columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="card")

        # Card 1: Status indicator
        self.status_card = self._make_card(cards_frame, "STATUS", "● Idle", Colors.FG_SECONDARY)
        self.status_card["frame"].grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        # Card 2: Next upload
        self.next_card = self._make_card(cards_frame, "NEXT UPLOAD", "--:--", Colors.ACCENT_BLUE)
        self.next_card["frame"].grid(row=0, column=1, padx=6, sticky="nsew")

        # Card 3: Countdown timer
        self.countdown_card = self._make_card(cards_frame, "COUNTDOWN", "--:--:--", Colors.ACCENT_CYAN)
        self.countdown_card["frame"].grid(row=0, column=2, padx=6, sticky="nsew")

        # Card 4: Uploads today
        self.count_card = self._make_card(cards_frame, "UPLOADS TODAY", "0", Colors.ACCENT_GREEN)
        self.count_card["frame"].grid(row=0, column=3, padx=6, sticky="nsew")

        # Card 5: Last upload
        self.last_card = self._make_card(cards_frame, "LAST UPLOAD", "Never", Colors.ACCENT_ORANGE)
        self.last_card["frame"].grid(row=0, column=4, padx=(6, 0), sticky="nsew")

        # Info strip
        info_strip = tk.Frame(self.root, bg=Colors.BG_CARD, padx=14, pady=8,
                              highlightbackground=Colors.BORDER, highlightthickness=1)
        info_strip.pack(fill=tk.X, padx=16, pady=(6, 0))

        tk.Label(info_strip, text=f"📧 {self.cfg['email']}    ",
                 font=("Segoe UI", 9), fg=Colors.FG_SECONDARY, bg=Colors.BG_CARD,
                 ).pack(side=tk.LEFT)
        tk.Label(info_strip, text=f"📄 {Path(self.cfg['resume_path']).name}    ",
                 font=("Segoe UI", 9), fg=Colors.FG_SECONDARY, bg=Colors.BG_CARD,
                 ).pack(side=tk.LEFT)
        # Store the schedule label so we can update it on config hot-reload
        self.schedule_label = tk.Label(info_strip,
                 text=f"⏰ {', '.join(self.cfg['schedule_times'])}",
                 font=("Segoe UI", 9, "bold"), fg=Colors.ACCENT_ORANGE, bg=Colors.BG_CARD,
                 )
        self.schedule_label.pack(side=tk.LEFT)

        # Button row
        btn_frame = tk.Frame(self.root, bg=Colors.BG_DARK, pady=10)
        btn_frame.pack(fill=tk.X, padx=16)

        btn_opts = dict(font=("Segoe UI", 11, "bold"), width=14, pady=8)

        self.start_btn = HoverButton(
            btn_frame, text="▶  Start",
            normal_bg=Colors.BTN_START_NORMAL,
            hover_bg=Colors.BTN_START_HOVER,
            active_bg=Colors.BTN_START_ACTIVE,
            command=self._on_start, **btn_opts,
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = HoverButton(
            btn_frame, text="⏹  Stop",
            normal_bg=Colors.BTN_STOP_NORMAL,
            hover_bg=Colors.BTN_STOP_HOVER,
            active_bg=Colors.BTN_STOP_ACTIVE,
            command=self._on_stop, **btn_opts,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.stop_btn.set_disabled(True)

        self.run_now_btn = HoverButton(
            btn_frame, text="⚡ Run Now",
            normal_bg=Colors.BTN_RUN_NORMAL,
            hover_bg=Colors.BTN_RUN_HOVER,
            active_bg=Colors.BTN_RUN_ACTIVE,
            command=self._on_run_now, **btn_opts,
        )
        self.run_now_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.quit_btn = HoverButton(
            btn_frame, text="✕  Quit",
            normal_bg=Colors.BTN_QUIT_NORMAL,
            hover_bg=Colors.BTN_QUIT_HOVER,
            active_bg=Colors.BTN_QUIT_ACTIVE,
            command=self._on_quit, **btn_opts,
        )
        self.quit_btn.pack(side=tk.RIGHT)

        # Log section
        log_header = tk.Frame(self.root, bg=Colors.BG_DARK)
        log_header.pack(fill=tk.X, padx=16, pady=(6, 2))

        tk.Label(log_header, text="📋  Activity Log",
                 font=("Segoe UI", 10, "bold"),
                 fg=Colors.FG_SECONDARY, bg=Colors.BG_DARK,
                 ).pack(side=tk.LEFT)

        # Clear log button
        self.clear_btn = HoverButton(
            log_header, text="Clear",
            normal_bg=Colors.BG_INPUT, hover_bg=Colors.BORDER,
            active_bg=Colors.BG_DARK, normal_fg=Colors.FG_SECONDARY,
            font=("Segoe UI", 9), width=6, pady=2,
            command=self._clear_log,
        )
        self.clear_btn.pack(side=tk.RIGHT)

        log_frame = tk.Frame(self.root, bg=Colors.BG_LOG,
                             highlightbackground=Colors.BORDER, highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        self.log_text = tk.Text(
            log_frame, bg=Colors.BG_LOG, fg=Colors.FG_PRIMARY,
            font=("Cascadia Code", 10), wrap=tk.WORD,
            insertbackground=Colors.FG_PRIMARY, relief=tk.FLAT,
            padx=10, pady=8, state=tk.DISABLED, spacing1=2, spacing3=2,
        )
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview,
                                 bg=Colors.BG_INPUT, troughcolor=Colors.BG_DARK,
                                 highlightbackground=Colors.BORDER)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Log text color tags
        self.log_text.tag_configure("info",    foreground=Colors.FG_PRIMARY)
        self.log_text.tag_configure("success", foreground=Colors.ACCENT_GREEN)
        self.log_text.tag_configure("error",   foreground=Colors.ACCENT_RED)
        self.log_text.tag_configure("warning", foreground=Colors.ACCENT_ORANGE)
        self.log_text.tag_configure("trigger", foreground=Colors.ACCENT_PURPLE)
        self.log_text.tag_configure("dim",     foreground=Colors.FG_MUTED)

        # Welcome message
        self.log("[INFO] Application ready.")
        self.log(f"[INFO] Scheduled times: {', '.join(self.cfg['schedule_times'])}")
        if self.cfg.get("telegram_bot_token") and self.cfg.get("telegram_chat_id"):
            self.log("[INFO] 📱 Telegram bot configured — NVite questions will be relayed.")
        else:
            self.log("[WARNING] Telegram not configured — NVite questions will be skipped.")
        self.log("[INFO] Click ▶ Start to begin scheduled uploads, or ⚡ Run Now for an immediate upload.")

    def _make_card(self, parent, title, value, value_color):
        """Create a small dashboard card with a title and value label."""
        frame = tk.Frame(parent, bg=Colors.BG_CARD, padx=12, pady=8,
                         highlightbackground=Colors.BORDER, highlightthickness=1)

        title_lbl = tk.Label(frame, text=title, font=("Segoe UI", 8, "bold"),
                             fg=Colors.FG_MUTED, bg=Colors.BG_CARD, anchor="w")
        title_lbl.pack(fill=tk.X)

        value_lbl = tk.Label(frame, text=value, font=("Segoe UI", 14, "bold"),
                             fg=value_color, bg=Colors.BG_CARD, anchor="w")
        value_lbl.pack(fill=tk.X)

        return {"frame": frame, "title": title_lbl, "value": value_lbl}

    def log(self, message):
        """Append a color-coded message to the log area."""
        def _append():
            self.log_text.configure(state=tk.NORMAL)

            # Determine tag from message prefix
            tag = "info"
            if "[SUCCESS]" in message:
                tag = "success"
            elif "[ERROR]" in message:
                tag = "error"
            elif "[WARN" in message:
                tag = "warning"
            elif "[TRIGGER]" in message:
                tag = "trigger"

            ts = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f" {ts}  ", "dim")
            self.log_text.insert(tk.END, f"{message}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)

        self.root.after(0, _append)

    def _clear_log(self):
        """Clear all text from the log area."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _start_config_watcher(self):
        """Start polling config.ini every 5 seconds for schedule changes."""
        self._check_config()

    def _check_config(self):
        """Read config.ini and update schedule times if they changed."""
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE, encoding="utf-8")
            times_raw = config.get("schedule", "times", fallback="09:00, 13:00, 16:00")
            new_times = sorted([t.strip() for t in times_raw.split(",") if t.strip()])

            old_times = self.cfg["schedule_times"]
            if new_times != old_times:
                self.cfg["schedule_times"] = new_times
                self.log(f"[INFO] ⚙ Schedule updated: {', '.join(new_times)}")
                self.schedule_label.configure(text=f"⏰ {', '.join(new_times)}")
        except Exception:
            pass  # Silently skip if config is being edited mid-write

        # Re-check every 5 seconds
        self.root.after(5000, self._check_config)

    def _update_clock(self):
        """Refresh the clock label every second."""
        now = datetime.now()
        self.clock_label.configure(text=now.strftime("%H:%M:%S  ·  %A, %d %b %Y"))

        # Update dashboard cards
        self._update_dashboard(now)

        self.root.after(1000, self._update_clock)

    def _update_dashboard(self, now):
        """Refresh the dashboard card values."""
        # Next upload time
        next_t = self._get_next_upload(now)
        self.next_card["value"].configure(text=next_t if next_t else "Done for today")

        # Countdown timer — live remaining time until next upload
        countdown_str = self._get_countdown(now)
        self.countdown_card["value"].configure(text=countdown_str)

        # Upload count
        self.count_card["value"].configure(text=str(self.scheduler.upload_count))

        # Last upload
        if self.scheduler.last_upload_time:
            self.last_card["value"].configure(
                text=self.scheduler.last_upload_time.strftime("%H:%M:%S"))
        else:
            self.last_card["value"].configure(text="Never")

    def _get_next_upload(self, now):
        """Find the next scheduled time that hasn't fired yet today."""
        for t in sorted(self.cfg["schedule_times"]):
            h, m = map(int, t.split(":"))
            scheduled = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if scheduled > now:
                return t
        return None

    def _get_countdown(self, now):
        """Calculate remaining time until the next scheduled upload."""
        times = sorted(self.cfg["schedule_times"])
        if not times:
            return "No schedule"

        # First: check if any time is still upcoming today
        for t in times:
            h, m = map(int, t.split(":"))
            scheduled = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if scheduled > now:
                return self._format_countdown(scheduled - now)

        # All today's times have passed — count down to tomorrow's first time
        first = times[0]
        h, m = map(int, first.split(":"))
        tomorrow = (now + timedelta(days=1)).replace(hour=h, minute=m, second=0, microsecond=0)
        return self._format_countdown(tomorrow - now)

    def _format_countdown(self, delta):
        """Format a timedelta into a human-readable countdown string."""
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

    def _set_activity(self, state):
        """Called from the scheduler thread to update activity state."""
        self._current_activity = state

    def _update_status_indicator(self):
        """Animate the status indicator based on current activity."""
        if self._current_activity == "uploading":
            self.status_card["value"].configure(text="● Uploading...", fg=Colors.ACCENT_CYAN)
            self.status_card["frame"].configure(
                highlightbackground=Colors.ACCENT_CYAN, highlightthickness=2)
        elif self.scheduler.is_running():
            self.status_card["value"].configure(text="● Running", fg=Colors.ACCENT_GREEN)
            self.status_card["frame"].configure(
                highlightbackground=Colors.ACCENT_GREEN, highlightthickness=2)
        else:
            self.status_card["value"].configure(text="● Idle", fg=Colors.FG_SECONDARY)
            self.status_card["frame"].configure(
                highlightbackground=Colors.BORDER, highlightthickness=1)

        self.root.after(500, self._update_status_indicator)

    def _on_start(self):
        """Start the scheduler — run one upload immediately AND start the scheduler."""
        self.start_btn.set_disabled(True)
        self.stop_btn.set_disabled(False)
        self._current_activity = "running"

        # Start the scheduler immediately so it doesn't miss any upcoming times
        self.scheduler.start()

        # Also do an immediate upload in a background thread
        self.log("[INFO] ▶ Starting — running initial upload now...")
        orchestrator = UploadOrchestrator(self.cfg, self.log, self._set_activity)
        thread = threading.Thread(
            target=orchestrator.run_once,
            daemon=True,
        )
        thread.start()

    def _on_stop(self):
        """Stop the scheduler."""
        self.scheduler.stop()
        self.start_btn.set_disabled(False)
        self.stop_btn.set_disabled(True)
        self._current_activity = "idle"

    def _on_run_now(self):
        """Trigger an immediate upload in a background thread."""
        self.log("[INFO] ⚡ Manual upload triggered!")
        orchestrator = UploadOrchestrator(self.cfg, self.log, self._set_activity)
        thread = threading.Thread(
            target=orchestrator.run_once,
            daemon=True,
        )
        thread.start()

    def _on_quit(self):
        """Stop scheduler and exit."""
        if self.scheduler.is_running():
            self.scheduler.stop()
        self.root.destroy()

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()
