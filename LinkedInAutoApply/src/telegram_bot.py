import json
import time
import urllib.error
import urllib.parse
import urllib.request

TELEGRAM_API_BASE = "https://api.telegram.org/bot"

class TelegramBot:
    """
    Lightweight Telegram Bot client using only urllib (no pip packages needed).
    Sends messages and waits for text replies from a specific chat.
    """

    def __init__(self, bot_token: str, chat_id: str, log_fn=print):
        self.bot_token = bot_token.strip() if bot_token else ""
        self.chat_id = chat_id.strip() if chat_id else ""
        self.log_fn = log_fn
        self._base = f"{TELEGRAM_API_BASE}{self.bot_token}"
        self._unreachable = False

    @property
    def is_configured(self) -> bool:
        """Return True if both token and chat_id are present and reachable."""
        if self._unreachable:
            return False
        return bool(self.bot_token) and bool(self.chat_id)

    def _api_call(self, method: str, params: dict | None = None) -> dict:
        """Make a GET request to the Telegram Bot API and return the JSON."""
        if self._unreachable:
            return {}

        url = f"{self._base}/{method}"
        if params:
            query = urllib.parse.urlencode(params)
            url = f"{url}?{query}"
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            self.log_fn(f"[WARNING] Telegram API error: {e}. Disabling Telegram for this run to avoid connection hangs.")
            self._unreachable = True
            return {}

    def _get_latest_update_id(self) -> int:
        """Fetch the latest update_id so we can ignore old messages."""
        data = self._api_call("getUpdates", {"offset": -1, "limit": 1})
        results = data.get("result", [])
        if results:
            return results[-1]["update_id"]
        return 0

    def send_message(self, text: str) -> bool:
        """Send a text message to the configured chat. Returns True on success."""
        if not self.is_configured:
            return False
        data = self._api_call("sendMessage", {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        })
        return data.get("ok", False)

    def ask_question(self, question: str, timeout_seconds: int = 300) -> str | None:
        """
        Send a question via Telegram and wait for a text reply.

        Returns the reply text, or None if timed out / error.
        Polls every 3 seconds for up to `timeout_seconds`.
        """
        if not self.is_configured:
            self.log_fn("[WARNING] Telegram not configured — skipping question.")
            return None

        # Get baseline so we only look at NEW messages
        baseline_id = self._get_latest_update_id()

        # Send the question
        self.send_message(
            f"❓ <b>LinkedIn Easy Apply Question</b>\n\n{question}\n\n<i>Reply with your answer:</i>"
        )
        self.log_fn("[INFO] 📨 Sent question to Telegram, waiting for reply...")

        start = time.time()
        consecutive_failures = 0
        while time.time() - start < timeout_seconds:
            data = self._api_call("getUpdates", {
                "offset": baseline_id + 1,
                "timeout": 3,
            })
            if not data or not data.get("ok", False):
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    self.log_fn("[ERROR] Telegram API connection issue detected (3 consecutive failures). Aborting question to continue applying next.")
                    return None
            else:
                consecutive_failures = 0

            for update in data.get("result", []):
                msg = update.get("message", {})
                chat = msg.get("chat", {})
                text = msg.get("text", "")
                # Only accept messages from our configured chat
                if str(chat.get("id")) == str(self.chat_id) and text:
                    self.log_fn(f"[INFO] 📩 Received Telegram reply: {text}")
                    # Acknowledge the update so it isn't returned again
                    self._api_call("getUpdates", {"offset": update["update_id"] + 1})
                    return text.strip()
            time.sleep(3)

        self.log_fn("[WARNING] Telegram reply timed out.")
        return None

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """Send a photo/screenshot to the Telegram chat using multipart/form-data."""
        if not self.is_configured:
            return False
        
        from pathlib import Path
        url = f"{self._base}/sendPhoto"
        
        try:
            with open(photo_path, "rb") as f:
                photo_data = f.read()
                
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            
            body = []
            body.append(f"--{boundary}".encode("utf-8"))
            body.append(f'Content-Disposition: form-data; name="chat_id"'.encode("utf-8"))
            body.append("".encode("utf-8"))
            body.append(str(self.chat_id).encode("utf-8"))
            
            if caption:
                body.append(f"--{boundary}".encode("utf-8"))
                body.append(f'Content-Disposition: form-data; name="caption"'.encode("utf-8"))
                body.append("".encode("utf-8"))
                body.append(caption.encode("utf-8"))
                
            body.append(f"--{boundary}".encode("utf-8"))
            body.append(f'Content-Disposition: form-data; name="photo"; filename="{Path(photo_path).name}"'.encode("utf-8"))
            body.append(f'Content-Type: image/png'.encode("utf-8"))
            body.append("".encode("utf-8"))
            body.append(photo_data)
            
            body.append(f"--{boundary}--".encode("utf-8"))
            body.append("".encode("utf-8"))
            
            payload = b"\r\n".join(body)
            
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Content-Length": str(len(payload))
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("ok", False)
                
        except Exception as e:
            self.log_fn(f"[ERROR] Failed to send photo to Telegram: {e}")
            self._unreachable = True
            return False
