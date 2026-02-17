# Quick Start Guide - Job Seeker Application
# ============================================

# STEP 1: Activate Virtual Environment
# -------------------------------------
# PowerShell:
.\venv\Scripts\Activate.ps1

# Command Prompt:
# .\venv\Scripts\activate.bat

# You should see (venv) in your prompt


# STEP 2: Install Dependencies (if not already done)
# ---------------------------------------------------
pip install -r requirements.txt


# STEP 3: Run the Application
# ----------------------------
python main.py


# STEP 4: When Done, Deactivate
# ------------------------------
# deactivate


# ============================================
# TROUBLESHOOTING
# ============================================

# If you get "cannot be loaded because running scripts is disabled":
# Run PowerShell as Administrator and execute:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activating again:
# .\venv\Scripts\Activate.ps1


# ============================================
# ALTERNATIVE: Run without activating manually
# ============================================
# You can run directly using the venv Python:
.\venv\Scripts\python.exe main.py
