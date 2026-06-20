"""
=============================================================
  LinkedIn Easy Apply Auto-Applier — Main Runner
=============================================================

This acts as the application's entry point, loading the OOP modules
and launching the Tkinter desktop GUI.
"""

import sys
from pathlib import Path

# Add root folder and venv packages to sys.path for resolution fallbacks
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

venv_site_packages = BASE_DIR / "venv" / "Lib" / "site-packages"
if venv_site_packages.exists() and str(venv_site_packages) not in sys.path:
    sys.path.insert(0, str(venv_site_packages))

from src.config import ConfigLoader
from src.gui import LinkedInApplierApp

def main():
    """Load configuration and execute the main desktop GUI application loop."""
    cfg = ConfigLoader.load()
    app = LinkedInApplierApp(cfg)
    app.run()

if __name__ == "__main__":
    main()
