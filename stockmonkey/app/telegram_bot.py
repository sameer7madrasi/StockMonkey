"""Telegram bot listener for StockMonkey.

Runs as a long-polling loop. Designed to be started as a background process
via LaunchAgent or manually:

    cd stockmonkey
    python -m app.telegram_bot

Commands (send via Telegram):
    stonks          — run an immediate stock brief
    watchlist       — show current tickers
    add MSFT        — add a ticker to the watchlist
    remove COST     — remove a ticker from the watchlist
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
_POLL_TIMEOUT = 30

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


# ── command handlers ─────────────────────────────────────────────────

def _handle_stonks() -> None:
    """Run the pipeline and send the result to Telegram."""
    _send("Running your stock brief now...")

    from app.run_watchlist import run_watchlist
    from app.watchlist import load_tickers
    from app.format_digest import format_digest_markdown

    tickers = load_tickers()
    if not tickers:
        _send("Watchlist is empty. Add tickers with `add TICKER`.")
        return

    try:
        digest = run_watchlist(tickers)
    except Exception as exc:
        _send(f"Pipeline failed: `{exc}`")
        return

    md_text = format_digest_markdown(digest)
    _send(md_text)

    digest_dir = _PROJECT_ROOT / "data" / "digests"
    digest_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (digest_dir / f"{date_str}_watchlist_digest.json").write_text(
        json.dumps(digest, indent=2), encoding="utf-8"
    )
    (digest_dir / f"{date_str}_watchlist_digest.md").write_text(
        md_text, encoding="utf-8"
    )


def _handle_watchlist() -> None:
    from app.watchlist import load_tickers
    tickers = load_tickers()
    if tickers:
        listing = "\n".join(f"• {t}" for t in tickers)
        _send(f"*Current watchlist:*\n{listing}")
    else:
        _send("Watchlist is empty. Add tickers with `add TICKER`.")


def _handle_add(ticker: str) -> None:
    from app.watchlist import add_ticker
    added, current = add_ticker(ticker)
    if added:
        listing = ", ".join(current)
        _send(f"Added *{ticker.upper()}*.\nWatchlist: {listing}")
    else:
        _send(f"*{ticker.upper()}* is already on the watchlist.")


def _handle_remove(ticker: str) -> None:
    from app.watchlist import remove_ticker
    removed, current = remove_ticker(ticker)
    if removed:
        listing = ", ".join(current) if current else "(empty)"
        _send(f"Removed *{ticker.upper()}*.\nWatchlist: {listing}")
    else:
        _send(f"*{ticker.upper()}* is not on the watchlist.")


def _handle_help() -> None:
    _send(
        "*StockMonkey commands:*\n"
        "• `stonks` — get an immediate stock brief\n"
        "• `watchlist` — show current tickers\n"
        "• `add TICKER` — add a ticker\n"
        "• `remove TICKER` — remove a ticker\n"
        "• `help` — show this message"
    )


# ── polling loop ─────────────────────────────────────────────────────

def _dispatch(text: str) -> None:
    """Route an incoming message to the right handler."""
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip().upper() if len(parts) > 1 else ""

    if "stonks" in cmd:
        _handle_stonks()
    elif cmd == "watchlist":
        _handle_watchlist()
    elif cmd == "add" and arg:
        _handle_add(arg)
    elif cmd == "remove" and arg:
        _handle_remove(arg)
    elif cmd == "help":
        _handle_help()


def poll() -> None:
    """Long-poll loop: listen for messages and dispatch commands."""
    if not _BOT_TOKEN or not _CHAT_ID:
        _log("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Exiting.")
        sys.exit(1)

    _log("Bot started. Listening for commands.")

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
                text = (msg.get("text") or "").strip()

                if chat_id != str(_CHAT_ID):
                    continue

                if not text:
                    continue

                _log(f"Message: '{text}'")
                try:
                    _dispatch(text)
                except Exception as exc:
                    _log(f"Command failed: {exc}")
                    _send(f"Something went wrong: `{exc}`")

        except (urllib.error.URLError, TimeoutError):
            time.sleep(5)
        except Exception as exc:
            _log(f"Poll error: {exc}")
            time.sleep(10)


if __name__ == "__main__":
    poll()
