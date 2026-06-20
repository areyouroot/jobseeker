@echo off
REM ============================================
REM   LinkedIn Easy Apply Auto-Applier - Setup
REM ============================================
REM   This script:
REM   1. Creates a Python virtual environment
REM   2. Installs Playwright
REM   3. Downloads Chromium browser for Playwright
REM ============================================

echo.
echo ===============================================
echo   LinkedIn Easy Apply Auto-Applier - Setup
echo ===============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment
echo [1/3] Creating virtual environment...
if exist "venv" (
    echo       Virtual environment already exists, skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo       Done!
)

REM Activate venv and install dependencies
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo       Done!

REM Install Playwright browsers (Chromium only)
echo [3/3] Installing Playwright Chromium browser...
playwright install chromium
if errorlevel 1 (
    echo [ERROR] Failed to install Playwright browsers.
    pause
    exit /b 1
)
echo       Done!

echo.
echo ===============================================
echo   Setup complete!
echo ===============================================
echo.
echo   Next steps:
echo   1. Edit config.ini with your LinkedIn credentials
echo   2. Place your resume in the "resume" folder
echo   3. Run: run.bat
echo.
pause
