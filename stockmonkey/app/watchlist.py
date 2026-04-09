"""Watchlist loading, normalization, and deduplication."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def load_tickers(cli_args: list[str] | None = None) -> list[str]:
    """Return a deduplicated, uppercased list of ticker symbols.

    Resolution order:
      1. CLI arguments (if any non-empty strings are provided)
      2. DEFAULT_TICKERS from .env  (comma-separated)
      3. Empty list
    """
    raw: list[str] = []

    if cli_args:
        raw = cli_args
    else:
        env_val = os.getenv("DEFAULT_TICKERS", "")
        if env_val.strip():
            raw = env_val.split(",")

    seen: set[str] = set()
    tickers: list[str] = []
    for t in raw:
        t = t.strip().upper()
        if t and t not in seen:
            seen.add(t)
            tickers.append(t)

    return tickers
