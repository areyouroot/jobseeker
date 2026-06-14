"""
=============================================================
  Naukri.com Resume Auto-Uploader — Scheduled Edition
=============================================================

This script provides a GUI application that:
  1. Reads login credentials and scheduled times from config.ini
  2. Shows a control panel with Start / Stop / Quit buttons
  3. Runs a background scheduler that uploads your resume at
     each configured time every day
  4. Launches a visible Chromium browser for each upload

Dependencies:
  - playwright (installed via pip)
  - Chromium browser (installed via 'playwright install chromium')
  - tkinter (bundled with Python on Windows)

Usage:
  Activate the virtual environment, then run:
      python naukri_uploader.py
"""

# ──────────────────────────────────────────────
#  Standard library imports
# ──────────────────────────────────────────────
import configparser       # For reading config.ini (INI file format)
import sys                # For exiting the script on errors
import time               # For delays between browser actions
import threading          # For running the scheduler in the background
import tkinter as tk      # For building the desktop GUI
from tkinter import messagebox  # For pop-up dialogs
from datetime import datetime   # For time comparisons
from pathlib import Path  # For cross-platform file path handling

# ──────────────────────────────────────────────
#  Third-party imports (from the virtual environment)
# ──────────────────────────────────────────────
from playwright.sync_api import (
    sync_playwright,                          # Main Playwright entry point
    TimeoutError as PlaywrightTimeoutError,   # Raised when element wait times out
)


# ──────────────────────────────────────────────
#  Constants — File paths & URLs
# ──────────────────────────────────────────────

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "config.ini"
RESUME_DIR = BASE_DIR / "resume"

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"


# ──────────────────────────────────────────────
#  Color Palette
# ──────────────────────────────────────────────

class Colors:
    """Centralized color definitions for the entire UI."""
    BG_DARK       = "#0d1117"    # GitHub-dark background
    BG_CARD       = "#161b22"    # Card / panel surface
    BG_LOG        = "#0d1117"    # Log area background
    BG_INPUT      = "#21262d"    # Input-like surfaces
    BORDER        = "#30363d"    # Subtle borders
    BORDER_FOCUS  = "#58a6ff"    # Focused border

    FG_PRIMARY    = "#f0f6fc"    # Bright primary text
    FG_SECONDARY  = "#8b949e"    # Dimmed secondary text
    FG_MUTED      = "#484f58"    # Very muted text

    ACCENT_BLUE   = "#58a6ff"    # Links, info highlights
    ACCENT_GREEN  = "#3fb950"    # Success, start
    ACCENT_RED    = "#f85149"    # Error, stop
    ACCENT_ORANGE = "#d29922"    # Warnings
    ACCENT_PURPLE = "#bc8cff"    # Triggers
    ACCENT_CYAN   = "#39d2c0"    # Special highlights

    # Button states (Start)
    BTN_START_NORMAL  = "#238636"
    BTN_START_HOVER   = "#2ea043"
    BTN_START_ACTIVE  = "#196c2e"

    # Button states (Stop)
    BTN_STOP_NORMAL   = "#da3633"
    BTN_STOP_HOVER    = "#f85149"
    BTN_STOP_ACTIVE   = "#b62324"

    # Button states (Run Now)
    BTN_RUN_NORMAL    = "#1f6feb"
    BTN_RUN_HOVER     = "#388bfd"
    BTN_RUN_ACTIVE    = "#1158c7"

    # Button states (Quit)
    BTN_QUIT_NORMAL   = "#30363d"
    BTN_QUIT_HOVER    = "#484f58"
    BTN_QUIT_ACTIVE   = "#21262d"


# ──────────────────────────────────────────────
#  Interactive Button Widget
# ──────────────────────────────────────────────

class HoverButton(tk.Button):
    """
    A custom tkinter Button with hover and active (pressed) color states.

    When the mouse enters the button, it shifts to the hover color.
    When clicked (held down), it shifts to a darker active color.
    When disabled, it appears dimmed and non-interactive.
    """

    def __init__(self, master, normal_bg, hover_bg, active_bg,
                 normal_fg="#ffffff", disabled_bg="#21262d", disabled_fg="#484f58",
                 **kwargs):
        super().__init__(master, bg=normal_bg, fg=normal_fg,
                         activebackground=active_bg, activeforeground=normal_fg,
                         relief=tk.FLAT, bd=0, cursor="hand2", **kwargs)

        # Store color states
        self._normal_bg = normal_bg
        self._hover_bg = hover_bg
        self._active_bg = active_bg
        self._normal_fg = normal_fg
        self._disabled_bg = disabled_bg
        self._disabled_fg = disabled_fg

        # Bind mouse events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, event):
        """Mouse enters the button area → show hover color."""
        if self.cget("state") != tk.DISABLED:
            self.configure(bg=self._hover_bg)

    def _on_leave(self, event):
        """Mouse leaves the button area → restore normal color."""
        if self.cget("state") != tk.DISABLED:
            self.configure(bg=self._normal_bg)

    def _on_press(self, event):
        """Mouse button pressed down → show dark active color."""
        if self.cget("state") != tk.DISABLED:
            self.configure(bg=self._active_bg)

    def _on_release(self, event):
        """Mouse button released → return to hover (mouse is still over button)."""
        if self.cget("state") != tk.DISABLED:
            self.configure(bg=self._hover_bg)

    def set_disabled(self, disabled: bool):
        """Enable or disable the button with proper visual feedback."""
        if disabled:
            self.configure(state=tk.DISABLED, bg=self._disabled_bg,
                           fg=self._disabled_fg, cursor="arrow")
        else:
            self.configure(state=tk.NORMAL, bg=self._normal_bg,
                           fg=self._normal_fg, cursor="hand2")


# ──────────────────────────────────────────────
#  Configuration Loader
# ──────────────────────────────────────────────

def load_config() -> dict:
    """
    Read and validate config.ini.

    Returns a dictionary with keys:
        - email, password, resume_path, slow_mo, timeout, schedule_times
    """
    if not CONFIG_FILE.exists():
        messagebox.showerror("Config Error", f"Config file not found:\n{CONFIG_FILE}")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")

    try:
        email = config.get("naukri", "email")
        password = config.get("naukri", "password")
        resume_filename = config.get("settings", "resume_filename", fallback="resume.pdf")
        slow_mo = config.getint("settings", "slow_mo", fallback=100)
        timeout = config.getint("settings", "timeout", fallback=30000)

        times_raw = config.get("schedule", "times", fallback="09:00, 13:00, 16:00")
        schedule_times = [t.strip() for t in times_raw.split(",") if t.strip()]

    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        messagebox.showerror("Config Error", f"Missing required config fields:\n{e}")
        sys.exit(1)

    if email == "your_email@example.com" or password == "your_password_here":
        messagebox.showerror("Config Error", "Update config.ini with real credentials.")
        sys.exit(1)

    resume_path = RESUME_DIR / resume_filename
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

    # Sort times chronologically so "next upload" logic works correctly
    schedule_times.sort()

    return {
        "email": email,
        "password": password,
        "resume_path": str(resume_path),
        "slow_mo": slow_mo,
        "timeout": timeout,
        "schedule_times": schedule_times,
    }


# ──────────────────────────────────────────────
#  Browser Automation — Login
# ──────────────────────────────────────────────

def login_to_naukri(page, email, password, timeout, log_fn=print) -> bool:
    """Log in to Naukri. Returns True on success."""
    log_fn("[INFO] Navigating to Naukri login page...")
    page.goto(NAUKRI_LOGIN_URL, wait_until="domcontentloaded", timeout=timeout)
    time.sleep(2)

    log_fn("[INFO] Entering email...")
    email_input = page.locator('#usernameField')
    email_input.wait_for(state="visible", timeout=timeout)
    email_input.click()
    email_input.fill(email)

    log_fn("[INFO] Entering password...")
    password_input = page.locator('#passwordField')
    password_input.wait_for(state="visible", timeout=timeout)
    password_input.click()
    password_input.fill(password)

    log_fn("[INFO] Clicking Login button...")
    login_button = page.locator('button[type="submit"].blue-btn')
    login_button.wait_for(state="visible", timeout=timeout)
    login_button.click()

    log_fn("[INFO] Waiting for login to complete...")
    try:
        page.wait_for_url("**/nlogin/login**", timeout=5000)
        error_msg = page.locator(".err-message, .error-msg, [class*='error']")
        if error_msg.is_visible():
            log_fn(f"[ERROR] Login failed: {error_msg.text_content()}")
            return False
    except PlaywrightTimeoutError:
        pass  # URL changed → login succeeded

    time.sleep(3)
    log_fn("[SUCCESS] Logged in successfully!")
    return True


# ──────────────────────────────────────────────
#  Browser Automation — Resume Upload
# ──────────────────────────────────────────────

def upload_resume(page, resume_path, timeout, log_fn=print) -> bool:
    """Upload the resume on the profile page. Returns True on success."""
    log_fn("[INFO] Navigating to profile page...")
    page.goto(NAUKRI_PROFILE_URL, wait_until="domcontentloaded", timeout=timeout)
    time.sleep(3)

    log_fn("[INFO] Looking for resume upload input...")
    file_input = page.locator('input[type="file"]').first

    try:
        log_fn(f"[INFO] Uploading resume...")
        file_input.set_input_files(resume_path)
        time.sleep(5)
        log_fn("[SUCCESS] Resume uploaded successfully!")
        return True

    except PlaywrightTimeoutError:
        log_fn("[WARNING] Direct upload failed, trying fallback...")
        try:
            update_btn = page.locator(
                'text="Update resume",'
                'text="Upload Resume",'
                '[class*="resume"] >> text="Update"'
            ).first
            update_btn.wait_for(state="visible", timeout=timeout)
            update_btn.click()
            time.sleep(2)
            file_input = page.locator('input[type="file"]').first
            file_input.set_input_files(resume_path)
            time.sleep(5)
            log_fn("[SUCCESS] Resume uploaded (fallback)!")
            return True
        except Exception as e:
            log_fn(f"[ERROR] Upload failed: {e}")
            return False


# ──────────────────────────────────────────────
#  Full Upload Workflow (one cycle)
# ──────────────────────────────────────────────

def run_upload_once(cfg, log_fn=print, status_fn=None):
    """Launch browser → login → upload → close."""

    if status_fn:
        status_fn("uploading")

    log_fn("[TRIGGER] Starting upload cycle...")

    with sync_playwright() as p:
        log_fn("[INFO] Launching browser...")
        browser = p.chromium.launch(
            headless=False,
            slow_mo=cfg["slow_mo"],
            args=["--start-maximized",
                  "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport=None,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            success = login_to_naukri(page, cfg["email"], cfg["password"],
                                      cfg["timeout"], log_fn)
            if success:
                upload_resume(page, cfg["resume_path"], cfg["timeout"], log_fn)
            else:
                log_fn("[ERROR] Login failed — skipping upload.")
        except Exception as e:
            log_fn(f"[ERROR] {e}")
        finally:
            time.sleep(2)
            context.close()
            browser.close()
            log_fn("[INFO] Browser closed.")

    if status_fn:
        status_fn("idle")


# ──────────────────────────────────────────────
#  Scheduler (background thread)
# ──────────────────────────────────────────────

class UploadScheduler:
    """
    Background scheduler — checks time every 30 seconds, fires uploads
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
        self._stop_event.set()
        self.log_fn("[INFO] Scheduler stopped.")

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _run_loop(self):
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
                        run_upload_once(self.cfg, self.log_fn, self.status_fn)
                        self.upload_count += 1
                        self.last_upload_time = datetime.now()
                    except Exception as e:
                        self.log_fn(f"[ERROR] Upload failed: {e}")

            # Poll every 10 seconds for more responsive timing
            self._stop_event.wait(timeout=10)


# ──────────────────────────────────────────────
#  GUI Application
# ──────────────────────────────────────────────

class NaukriUploaderApp:
    """
    Desktop GUI with interactive buttons, live log, status dashboard,
    and hover/active visual feedback.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.scheduler = UploadScheduler(cfg, log_fn=self.log, status_fn=self._set_activity)
        self._current_activity = "idle"  # idle | running | uploading

        # ── Main window ──
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

        # Check for command line arguments to auto-start
        if len(sys.argv) > 1 and sys.argv[1] in ("--start", "-s"):
            self.root.after(150, self._on_start)

    # ──────────────────────────────────────
    #  UI Construction
    # ──────────────────────────────────────

    def _build_ui(self):
        """Build all UI components."""

        # ── Title bar ──
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

        # ── Status Dashboard ──
        dashboard = tk.Frame(self.root, bg=Colors.BG_DARK, pady=8)
        dashboard.pack(fill=tk.X, padx=16)

        # --- Row of status cards ---
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

        # ── Info strip ──
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

        # ── Button row ──
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

        # ── Log section ──
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

        # --- Log text color tags ---
        self.log_text.tag_configure("info",    foreground=Colors.FG_PRIMARY)
        self.log_text.tag_configure("success", foreground=Colors.ACCENT_GREEN)
        self.log_text.tag_configure("error",   foreground=Colors.ACCENT_RED)
        self.log_text.tag_configure("warning", foreground=Colors.ACCENT_ORANGE)
        self.log_text.tag_configure("trigger", foreground=Colors.ACCENT_PURPLE)
        self.log_text.tag_configure("dim",     foreground=Colors.FG_MUTED)

        # ── Welcome message ──
        self.log("[INFO] Application ready.")
        self.log(f"[INFO] Scheduled times: {', '.join(self.cfg['schedule_times'])}")
        self.log("[INFO] Click ▶ Start to begin scheduled uploads, or ⚡ Run Now for an immediate upload.")

    # ──────────────────────────────────────
    #  Status Card Builder
    # ──────────────────────────────────────

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

    # ──────────────────────────────────────
    #  Logging (thread-safe)
    # ──────────────────────────────────────

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

    # ──────────────────────────────────────
    #  Config Hot-Reload
    # ──────────────────────────────────────

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
                # Also update the scheduler's reference (it shares cfg dict)
                self.log(f"[INFO] ⚙ Schedule updated: {', '.join(new_times)}")
                # Update the info strip label
                self.schedule_label.configure(text=f"⏰ {', '.join(new_times)}")
        except Exception:
            pass  # Silently skip if config is being edited mid-write

        # Re-check every 5 seconds
        self.root.after(5000, self._check_config)

    # ──────────────────────────────────────
    #  Live Clock & Dashboard Updates
    # ──────────────────────────────────────

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
        from datetime import timedelta
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

    # ──────────────────────────────────────
    #  Status Indicator Animation
    # ──────────────────────────────────────

    def _set_activity(self, state):
        """Called from the scheduler thread to update activity state."""
        self._current_activity = state

    def _update_status_indicator(self):
        """Animate the status indicator based on current activity."""
        if self._current_activity == "uploading":
            # Pulsing cyan dot when actively uploading
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

    # ──────────────────────────────────────
    #  Button Handlers
    # ──────────────────────────────────────

    def _on_start(self):
        """Start the scheduler — run one upload immediately AND start the scheduler."""
        self.start_btn.set_disabled(True)
        self.stop_btn.set_disabled(False)
        self._current_activity = "running"

        # Start the scheduler immediately so it doesn't miss any upcoming times
        self.scheduler.start()

        # Also do an immediate upload in a background thread
        self.log("[INFO] ▶ Starting — running initial upload now...")
        thread = threading.Thread(
            target=run_upload_once,
            args=(self.cfg, self.log, self._set_activity),
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
        thread = threading.Thread(
            target=run_upload_once,
            args=(self.cfg, self.log, self._set_activity),
            daemon=True,
        )
        thread.start()

    def _on_quit(self):
        """Stop scheduler and exit."""
        if self.scheduler.is_running():
            self.scheduler.stop()
        self.root.destroy()

    # ──────────────────────────────────────
    #  Run
    # ──────────────────────────────────────

    def run(self):
        """Start the tkinter main loop."""
        self.root.mainloop()


# ──────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────

def main():
    cfg = load_config()
    app = NaukriUploaderApp(cfg)
    app.run()


if __name__ == "__main__":
    main()
