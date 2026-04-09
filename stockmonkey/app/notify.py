"""Telegram notification delivery for daily briefs."""
from __future__ import annotations

import os
import urllib.request
import urllib.parse
import json

from dotenv import load_dotenv

load_dotenv()

_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

_MAX_MESSAGE_LENGTH = 4096


def _send_telegram(text: str, parse_mode: str = "Markdown") -> bool:
    """Send a message via the Telegram Bot API. Returns True on success."""
    if not _BOT_TOKEN or not _CHAT_ID:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping notification")
        return False

    url = f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage"

    # Telegram has a 4096-char limit per message; truncate if needed
    if len(text) > _MAX_MESSAGE_LENGTH:
        text = text[: _MAX_MESSAGE_LENGTH - 20] + "\n\n_(truncated)_"

    payload = json.dumps({
        "chat_id": int(_CHAT_ID),
        "text": text,
        "parse_mode": parse_mode,
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
            return body.get("ok", False)
    except Exception as exc:
        print(f"Telegram send failed: {exc}")
        return False


def send_brief(digest: dict, markdown_text: str) -> bool:
    """Format and send the daily brief to Telegram."""
    return _send_telegram(markdown_text)
