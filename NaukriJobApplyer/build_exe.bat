@echo off
echo Building naukri_uploader.exe...

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install PyInstaller if not already installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Build the executable
echo Running PyInstaller...
pyinstaller --onefile --windowed --icon=NONE naukri_uploader.py

echo.
echo Build complete! The executable can be found in the "dist" folder.
pause
