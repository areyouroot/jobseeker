# 🚀 Naukri.com Resume Auto-Uploader & Job Applier

Automatically log in to your [Naukri.com](https://www.naukri.com) account, upload/update your resume, extract job keywords using a local LLM, and apply to jobs automatically — powered by **Python** and **Playwright**.

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
  - [Config Fields Explained](#config-fields-explained)
  - [Setting Up Telegram Bot Integration (Optional)](#setting-up-telegram-bot-integration-optional)
  - [Setting Up LLM Integration (Optional)](#setting-up-llm-integration-optional)
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
- **Config-driven** — Credentials, schedules, settings, and delays live in `config.ini`.
- **Hot-reloading Schedules** — Edits to schedule times in `config.ini` are picked up live without restarting the application!
- **Recruiter NVites Checker** — Automatically checks for pending recruiter invitations and accepts them.
- **Local LLM Keyword Extraction** — Uses a local LLM chat webhook to analyze your PDF resume and extract relevant job search keywords.
- **Automated Job Search & Application**:
  - Searches Naukri for extracted keywords.
  - Applies to up to **3 jobs per keyword** (maximum of 15 successful applications per session).
  - Handles external career site redirects by forwarding links to your Telegram and skipping.
  - Relays pre-screening questions to Telegram with a **2-hour timeout**.
  - Automatically captures screenshots of the browser on failure and posts them to your Telegram.
- **Configurable Delays** — Set pause timers after uploading the resume and after applying to each job directly in the configuration.
- **Resume folder** — Keep your resume(s) organised in a dedicated `resume/` directory.
- **Error handling** — Graceful timeouts, login-failure detection, and manual-fallback prompts.
- **Anti-detection basics** — Uses a realistic user-agent string and disables the `AutomationControlled` flag.

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

The project has been refactored into a highly clean, modular, and easy-to-read Object-Oriented Programming (OOP) design adhering to single-responsibility principles:

```
NaukriJobApplyer/
│
├── config.ini              # Your Naukri credentials, schedules & settings
├── config.ini-eg           # Template example config
├── naukri_uploader.py      # Main entry point runner script
├── requirements.txt        # Python package dependencies
├── setup.bat               # One-time environment setup batch script
├── run.bat                 # Shortcut launcher for the application
├── README.md               # This file
│
├── resume/                 # Place your resume PDF/Doc here
│   └── resume.pdf
│
└── src/                    # Core OOP package classes
    ├── __init__.py         # Package initializer
    ├── colors.py           # Centralized hex color palette (Colors)
    ├── widgets.py          # Custom tkinter widgets (HoverButton)
    ├── config.py           # Configuration loading & validation logic (ConfigLoader)
    ├── llm_client.py       # PDF parser & LLM webhook communicator (LLMClient)
    ├── telegram_bot.py     # Telegram Bot communicator, supports photo uploads (TelegramBot)
    │
    ├── automation/         # Browser automation components
    │   ├── browser_controller.py# Playwright browser manager (NaukriBrowser)
    │   ├── session.py      # Naukri login workflow handler (NaukriSession)
    │   ├── uploader.py     # Resume profile upload logic (ResumeUploader)
    │   ├── nvite_handler.py# Invites scanner and handler (NViteHandler)
    │   ├── screening_handler.py # Screen question modal handler (ScreeningHandler)
    │   └── job_applier.py  # Keywords job search and apply automation (JobApplier)
    │
    ├── orchestrator.py     # Integrates login, upload, and checks (UploadOrchestrator)
    ├── scheduler.py        # Background scheduler clock thread (UploadScheduler)
    └── gui.py              # Tkinter GUI interface, dashboard, and logs (NaukriUploaderApp)
```

---

## 📦 Installation

### Option A — Using `setup.bat` (Recommended)

1. **Double-click `setup.bat`** in the project folder.
2. It will automatically:
   - Create a Python virtual environment (`venv/`)
   - Install Playwright, `pypdf`, and other dependencies
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

---

## ⚙️ Configuration

Open **`config.ini`** in any text editor and fill in your real Naukri credentials and preferences:

```ini
[naukri]
email = your_actual_email@example.com
password = your_actual_password

[settings]
resume_filename = resume.pdf
slow_mo = 100
timeout = 30000
upload_delay = 10
apply_delay = 60

[schedule]
# Comma-separated times in 24-hour HH:MM format
times = 09:00, 13:00, 16:00

[telegram]
bot_token = YOUR_TELEGRAM_BOT_TOKEN
chat_id = YOUR_TELEGRAM_CHAT_ID

[llm]
url = http://localhost:5678/webhook/chat
```

### Config Fields Explained

| Field | Section | Description |
| --- | --- | --- |
| `email` | `[naukri]` | Your Naukri login email or username |
| `password` | `[naukri]` | Your Naukri account password |
| `resume_filename` | `[settings]`| The exact filename of your resume inside the `resume/` folder |
| `slow_mo` | `[settings]`| Milliseconds to pause between each browser action (default: `100`) |
| `timeout` | `[settings]`| Max wait time in ms for page elements to load (default: `30000` = 30 sec)|
| `upload_delay` | `[settings]`| Delay in seconds to sleep after uploading the resume (default: `10` sec)|
| `apply_delay` | `[settings]`| Delay in seconds to sleep after applying to each job (default: `60` sec)|
| `times` | `[schedule]`| Comma-separated 24-hour timestamps to run the uploads/applications |
| `bot_token` | `[telegram]`| (Optional) HTTP API bot token from Telegram's `@BotFather` |
| `chat_id` | `[telegram]`| (Optional) Your personal Telegram numeric chat ID from `@userinfobot` |
| `url` | `[llm]` | (Optional) URL of your local LLM model/webhook for keyword extraction |

> ⚠️ **Security Note:** `config.ini` contains your password in plain text. Do **not** commit it to a public repository. It is included in `.gitignore` by default.

---

### Setting Up Telegram Bot Integration (Optional)

The uploader includes a Telegram integration to notify you of actions, relay recruiter questions, and send browser screenshots on failure.

#### Step-by-Step Setup Guide

1. **Create a Telegram Bot**:
   - Open Telegram and search for the official **@BotFather** bot.
   - Send `/newbot` to start the bot creation process.
   - Follow the prompts to specify a name and a username for your bot.
   - Copy the generated **HTTP API Token** (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). This is your `bot_token`.

2. **Get Your Personal Chat ID**:
   - Search for the **@userinfobot** or **@GetIdsBot** on Telegram.
   - Send `/start` or any text message to it.
   - The bot will reply with your personal **Id** (a long number, e.g., `987654321`). This is your `chat_id`.

3. **Start the Conversation with Your Bot**:
   - Navigate to your custom bot's chat interface (using the link provided by `@BotFather` or searching its username in Telegram).
   - Press the **Start** button or send `/start` to authorize the bot to send you messages. **If you skip this step, the bot will not be able to message you.**

4. **Insert values in `config.ini`**:
   - Add your bot token and chat ID to the `[telegram]` section of your configuration file.

---

### Setting Up LLM Integration (Optional)

If the `[llm]` section's `url` is configured in `config.ini`, the application will perform the job search and apply workflow.

#### How It Works
1. **Resume Analysis**: The app reads your resume PDF text using `pypdf`.
2. **LLM Query**: It sends a POST request to your LLM webhook containing the resume and matching the required structure:
   ```json
   [
     {
       "systemMessage": "You are a job searching agent",
       "prompt": "Extract job keywords..."
     }
   ]
   ```
3. **Keyword Extraction**: The LLM analyzes your resume and responds with a list of search keywords.
4. **Job Application**: The app searches Naukri for each keyword, visits job description pages, clicks "Apply", and sleeps `apply_delay` seconds after each successful application.
5. **Screening Questions Relay**: If the application requires screening questions, they are sent to your Telegram chat. The app will wait up to **2 hours** for you to respond before skipping.
6. **External Redirects**: If the job redirects to an external company website, the app captures the link, sends it to your Telegram, and proceeds to the next job.
7. **Failure Screenshots**: If any step in the login, upload, or application flows fails, the browser automatically takes a screenshot and uploads it to your Telegram.

---

## 📄 Adding Your Resume

1. Place your resume file (e.g., `resume.pdf`) into the **`resume/`** folder.
2. Make sure the filename in `config.ini` matches exactly:
   ```ini
   resume_filename = resume.pdf
   ```

---

## ▶️ Running the Script

### Option A — Using `run.bat`

1. **Double-click `run.bat`** in the project folder.
2. The desktop control panel application will launch.
3. Click **▶ Start** to activate scheduled runs (it also fires an immediate verification upload). Or click **⚡ Run Now** to execute a manual upload/search cycle immediately.

### Option B — Running Manually

```powershell
# Activate the virtual environment
.\venv\Scripts\activate

# Run the script
python naukri_uploader.py
```

---

## ⚠️ Disclaimer

This tool is for **personal use only**. Automating interactions with Naukri.com may be against their Terms of Service. Use at your own risk. The authors are not responsible for any account restrictions or other consequences.

---

**Happy job hunting! 🎯**
