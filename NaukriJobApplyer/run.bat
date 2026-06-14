@echo off
cd /d "x:\git\jobseeker\NaukriJobApplyer"

echo.
echo ===============================================
echo   Naukri Resume Uploader - Starting...
echo ===============================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo         Please run setup.bat first.
    pause
    exit /b 1
)

REM Activate venv and run the script
call venv\Scripts\activate.bat
python naukri_uploader.py --start

echo.
pause
