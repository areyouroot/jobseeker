"""
=============================================================
  Utility: Test Telegram Connection
=============================================================

This script loads the credentials from config.ini and sends a
test message to verify that your Telegram bot is working and
properly configured.

Usage:
  python test/test_telegram_connection.py
"""

import sys
from pathlib import Path

# Add project root directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ConfigLoader
from src.telegram_bot import TelegramBot

def run_test():
    print("[INFO] Loading config.ini...")
    try:
        cfg = ConfigLoader.load()
    except SystemExit:
        print("[ERROR] Failed to load config.ini or config.ini validation failed.")
        return

    bot_token = cfg.get("telegram_bot_token", "").strip()
    chat_id = cfg.get("telegram_chat_id", "").strip()

    if not bot_token or not chat_id:
        print("[ERROR] Telegram credentials are not configured in config.ini!")
        print("Please configure bot_token and chat_id in config.ini first.")
        return

    print(f"[INFO] Initializing Telegram Bot (Chat ID: {chat_id})...")
    bot = TelegramBot(bot_token=bot_token, chat_id=chat_id, log_fn=print)

    print("[INFO] Sending test message...")
    success = bot.send_message(
        "👋 <b>Naukri Auto-Uploader Test</b>\n\n"
        "Hi! If you received this, your Telegram integration is working perfectly!"
    )

    if success:
        print("[SUCCESS] Test message sent to your Telegram chat successfully.")
    else:
        print("[ERROR] Failed! Message could not be sent. Please double check:")
        print("  1. The bot_token and chat_id values in config.ini are correct.")
        print("  2. You have pressed 'Start' (or sent /start) on Telegram to your bot.")
        print("  3. Your computer is connected to the internet.")

if __name__ == "__main__":
    run_test()
