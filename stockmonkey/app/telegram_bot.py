"""Telegram bot listener: responds to 'stonks' with an on-demand daily brief.

Runs as a long-polling loop. Designed to be started as a background process
via LaunchAgent or manually:

    cd stockmonkey
    python -m app.telegram_bot

Send 'stonks' to the bot on Telegram to trigger an immediate update.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
_TRIGGER_WORD = "stonks"
_POLL_TIMEOUT = 30  # seconds to hold the long-poll connection

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LOG_FILE = _PROJECT_ROOT / "logs" / "telegram_bot.log"


def _log(msg: str) -> None:
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(_LOG_FILE, "a") as f:
        f.write(line + "\n")


def _api(method: str, params: dict | None = None, timeout: int = 35) -> dict:
    url = f"https://api.telegram.org/bot{_BOT_TOKEN}/{method}"
    if params:
        data = json.dumps(params).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
    else:
        req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _send(text: str, parse_mode: str = "Markdown") -> None:
    if len(text) > 4096:
        text = text[:4076] + "\n\n_(truncated)_"
    _api("sendMessage", {
        "chat_id": int(_CHAT_ID),
        "text": text,
        "parse_mode": parse_mode,
    })


def _handle_stonks() -> None:
    """Run the pipeline and send the result to Telegram."""
    _send("Running your stock brief now...")

    # Import here to avoid circular imports and heavy init at startup
    from app.run_watchlist import run_watchlist
    from app.watchlist import load_tickers
    from app.format_digest import format_digest_markdown

    tickers = load_tickers()
    if not tickers:
        _send("No tickers configured. Set DEFAULT\\_TICKERS in .env.")
        return

    try:
        digest = run_watchlist(tickers)
    except Exception as exc:
        _send(f"Pipeline failed: `{exc}`")
        return

    md_text = format_digest_markdown(digest)
    _send(md_text)

    # Save artifacts too
    digest_dir = _PROJECT_ROOT / "data" / "digests"
    digest_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (digest_dir / f"{date_str}_watchlist_digest.json").write_text(
        json.dumps(digest, indent=2), encoding="utf-8"
    )
    (digest_dir / f"{date_str}_watchlist_digest.md").write_text(
        md_text, encoding="utf-8"
    )


def poll() -> None:
    """Long-poll loop: listen for messages and respond to the trigger word."""
    if not _BOT_TOKEN or not _CHAT_ID:
        _log("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Exiting.")
        sys.exit(1)

    _log(f"Bot started. Listening for '{_TRIGGER_WORD}' from chat {_CHAT_ID}")

    offset = 0
    while True:
        try:
            result = _api("getUpdates", {
                "offset": offset,
                "timeout": _POLL_TIMEOUT,
            }, timeout=_POLL_TIMEOUT + 5)

            for update in result.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text = (msg.get("text") or "").strip().lower()

                if chat_id != str(_CHAT_ID):
                    continue

                if _TRIGGER_WORD in text:
                    _log(f"Trigger received: '{msg.get('text')}'")
                    try:
                        _handle_stonks()
                        _log("Brief sent successfully")
                    except Exception as exc:
                        _log(f"Brief failed: {exc}")
                        _send(f"Something went wrong: `{exc}`")

        except (urllib.error.URLError, TimeoutError):
            time.sleep(5)
        except Exception as exc:
            _log(f"Poll error: {exc}")
            time.sleep(10)


if __name__ == "__main__":
    poll()
