@echo off
REM ============================================
REM   LinkedIn Easy Apply Auto-Applier - Run
REM ============================================

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python linkedin_applier.py
pause
