"""Watchlist loading, normalization, and mutation.

Resolution order for loading tickers:
  1. CLI arguments (if provided)
  2. data/watchlist.json (the live watchlist, editable via Telegram bot)
  3. DEFAULT_TICKERS from .env (initial fallback)
  4. Empty list
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_WATCHLIST_PATH = Path(__file__).resolve().parent.parent / "data" / "watchlist.json"


def _dedup(raw: list[str]) -> list[str]:
    seen: set[str] = set()
    tickers: list[str] = []
    for t in raw:
        t = t.strip().upper()
        if t and t not in seen:
            seen.add(t)
            tickers.append(t)
    return tickers


def _read_watchlist_file() -> list[str] | None:
    """Read tickers from data/watchlist.json. Returns None if file is missing."""
    if not _WATCHLIST_PATH.exists():
        return None
    try:
        data = json.loads(_WATCHLIST_PATH.read_text(encoding="utf-8"))
        return data.get("tickers", [])
    except (json.JSONDecodeError, KeyError):
        return None


def _write_watchlist_file(tickers: list[str]) -> None:
    _WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    _WATCHLIST_PATH.write_text(
        json.dumps({"tickers": tickers}, indent=2) + "\n", encoding="utf-8"
    )


def load_tickers(cli_args: list[str] | None = None) -> list[str]:
    """Return a deduplicated, uppercased list of ticker symbols."""
    if cli_args:
        return _dedup(cli_args)

    from_file = _read_watchlist_file()
    if from_file:
        return _dedup(from_file)

    env_val = os.getenv("DEFAULT_TICKERS", "")
    if env_val.strip():
        return _dedup(env_val.split(","))

    return []


def add_ticker(ticker: str) -> tuple[bool, list[str]]:
    """Add a ticker to the watchlist. Returns (was_added, current_list)."""
    current = load_tickers()
    ticker = ticker.strip().upper()
    if ticker in current:
        return False, current
    current.append(ticker)
    _write_watchlist_file(current)
    return True, current


def remove_ticker(ticker: str) -> tuple[bool, list[str]]:
    """Remove a ticker from the watchlist. Returns (was_removed, current_list)."""
    current = load_tickers()
    ticker = ticker.strip().upper()
    if ticker not in current:
        return False, current
    current.remove(ticker)
    _write_watchlist_file(current)
    return True, current
