# 🚀 Naukri.com Resume Auto-Uploader

Automatically log in to your [Naukri.com](https://www.naukri.com) account and upload/update your resume — powered by **Python** and **Playwright**.

The browser runs in **visible mode** so you can watch every step as it happens.

---

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
  - [Option A — Using setup.bat (Recommended)](#option-a--using-setupbat-recommended)
  - [Option B — Manual Setup](#option-b--manual-setup)
- [Configuration](#-configuration)
- [Adding Your Resume](#-adding-your-resume)
- [Running the Script](#-running-the-script)
  - [Option A — Using run.bat](#option-a--using-runbat)
  - [Option B — Running Manually](#option-b--running-manually)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Disclaimer](#-disclaimer)

---

## ✨ Features

- **Visible Browser** — Launches a real Chromium window; nothing runs hidden.
- **Config-driven** — Credentials and settings live in `config.ini`, not hard-coded.
- **Resume folder** — Keep your resume(s) organised in a dedicated `resume/` directory.
- **Error handling** — Graceful timeouts, login-failure detection, and manual-fallback prompts.
- **Anti-detection basics** — Uses a realistic user-agent string and disables the `AutomationControlled` flag.
- **One-click setup & run** — Batch files for Windows so you don't need to memorise commands.

---

## 🔧 Prerequisites

| Requirement    | Minimum Version | How to Check           |
| -------------- | --------------- | ---------------------- |
| **Python**     | 3.8+            | `python --version`     |
| **pip**        | (bundled)       | `pip --version`        |
| **Windows OS** | 10 / 11         | —                      |
| **Internet**   | Required        | For login & downloads  |

> **Don't have Python?**  
> Download it from [python.org](https://www.python.org/downloads/).  
> During installation, **check "Add Python to PATH"** — this is critical.

---

## 📁 Project Structure

```
nakukriTest/
│
├── config.ini              # Your Naukri credentials & settings
├── naukri_uploader.py      # Main automation script (Playwright)
├── requirements.txt        # Python package dependencies
├── setup.bat               # One-time setup: venv + install + browser
├── run.bat                 # Run the uploader with one click
├── README.md               # This file
│
├── resume/                 # ← Place your resume PDF here
│   └── resume.pdf
│
└── venv/                   # Python virtual environment (auto-created)
    └── ...
```

---

## 📦 Installation

### Option A — Using `setup.bat` (Recommended)

1. **Double-click `setup.bat`** in the project folder.
2. It will automatically:
   - Create a Python virtual environment (`venv/`)
   - Install Playwright and its dependencies
   - Download the Chromium browser binary
3. Wait for the "Setup complete!" message.

### Option B — Manual Setup

Open **PowerShell** or **Command Prompt**, `cd` into the project folder, and run:

```powershell
# Step 1 — Create the virtual environment
python -m venv venv

# Step 2 — Activate the virtual environment
.\venv\Scripts\activate

# Step 3 — Install Python dependencies
pip install -r requirements.txt

# Step 4 — Download Chromium for Playwright
playwright install chromium
```

> **Tip:** You only need to do this once. After setup, jump straight to [Running the Script](#-running-the-script).

---

## ⚙️ Configuration

Open **`config.ini`** in any text editor and fill in your real Naukri credentials:

```ini
[naukri]
email = your_actual_email@example.com
password = your_actual_password

[settings]
# Name of the resume file inside the resume/ folder
resume_filename = resume.pdf

# Slow-motion delay (ms) between browser actions — higher = slower & easier to watch
slow_mo = 100

# Maximum wait time (ms) for any element to appear on the page
timeout = 30000
```

### Config Fields Explained

| Field              | Section    | Description                                                                 |
| ------------------ | ---------- | --------------------------------------------------------------------------- |
| `email`            | `[naukri]` | Your Naukri login email or username                                         |
| `password`         | `[naukri]` | Your Naukri account password                                                |
| `resume_filename`  | `[settings]` | The exact filename of your resume inside the `resume/` folder            |
| `slow_mo`          | `[settings]` | Milliseconds to pause between each browser action (default: `100`)       |
| `timeout`          | `[settings]` | Max wait time in ms for page elements to load (default: `30000` = 30 sec)|

> ⚠️ **Security Note:** `config.ini` contains your password in plain text. Do **not** commit it to a public repository. Add it to `.gitignore` if using Git.

---

## 📄 Adding Your Resume

1. Place your resume file (e.g., `resume.pdf`) into the **`resume/`** folder.
2. Make sure the filename in `config.ini` matches exactly:
   ```ini
   resume_filename = resume.pdf
   ```
3. Supported formats: `.pdf`, `.doc`, `.docx` (whatever Naukri accepts).

> To update your resume later, simply replace the file in `resume/` and run the script again.

---

## ▶️ Running the Script

### Option A — Using `run.bat`

1. **Double-click `run.bat`** in the project folder.
2. A Chromium browser window will open and you can watch the automation.
3. After the resume is uploaded, the script will wait for you to **press Enter** before closing the browser.

### Option B — Running Manually

```powershell
# Activate the virtual environment
.\venv\Scripts\activate

# Run the script
python naukri_uploader.py
```

### What Happens When You Run It

```
Step 1  →  Browser launches (visible Chromium window)
Step 2  →  Navigates to https://www.naukri.com/nlogin/login
Step 3  →  Enters your email and password
Step 4  →  Clicks the Login button
Step 5  →  Navigates to your profile page
Step 6  →  Finds the resume upload input and uploads your file
Step 7  →  Waits for you to press Enter, then closes the browser
```

---

## 🔍 Troubleshooting

### "Python is not installed or not in PATH"

- Install Python from [python.org](https://www.python.org/downloads/).
- During installation, **check the box** that says "Add Python to PATH".
- Restart your terminal after installation.

### "Config file not found"

- Make sure `config.ini` exists in the same folder as `naukri_uploader.py`.
- It must not be renamed or moved.

### "Please update config.ini with your actual Naukri credentials"

- Open `config.ini` and replace the placeholder email/password with your real credentials.

### "Resume file not found"

- Ensure your resume file is inside the `resume/` folder.
- Check that the filename in `config.ini → resume_filename` matches exactly (case-sensitive).

### Login fails or times out

- Naukri may show a CAPTCHA or OTP challenge. The script keeps the browser open so you can **complete it manually**.
- If Naukri changes their page layout, the selectors in the script may need updating.
- Try increasing `timeout` in `config.ini` if your internet is slow.

### "Virtual environment not found"

- Run `setup.bat` first, or create the venv manually (see [Manual Setup](#option-b--manual-setup)).

### Browser doesn't open

- Make sure Chromium was installed: run `.\venv\Scripts\playwright.exe install chromium`
- Check your antivirus isn't blocking the Playwright browser.

---

## ❓ FAQ

**Q: Is this safe?**  
A: The script runs a real browser on your machine. Your credentials are stored locally in `config.ini` and are never sent anywhere except to Naukri's own login page.

**Q: Can I run this on a schedule?**  
A: Yes! Use Windows Task Scheduler to run `run.bat` at a set time (e.g., daily). Note that the script waits for Enter at the end — you may want to remove that `input()` call for fully unattended runs.

**Q: Does this work on Mac/Linux?**  
A: The Python script (`naukri_uploader.py`) is cross-platform. The `.bat` files are Windows-only, but you can replicate them with simple shell scripts.

**Q: What if Naukri changes their website?**  
A: You may need to update the CSS selectors/locators in `naukri_uploader.py`. Open the browser's DevTools (F12) to inspect the current page structure.

**Q: Can I upload a .docx instead of .pdf?**  
A: Yes — just put the `.docx` file in the `resume/` folder and update `resume_filename` in `config.ini`.

---

## ⚠️ Disclaimer

This tool is for **personal use only**. Automating interactions with Naukri.com may be against their Terms of Service. Use at your own risk. The authors are not responsible for any account restrictions or other consequences.

---

**Happy job hunting! 🎯**
