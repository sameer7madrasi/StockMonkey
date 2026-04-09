"""CLI entry point: extract a single ticker from Yahoo Finance."""
from __future__ import annotations

import sys

from app.yahoo_finance import extract_ticker


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    snap = extract_ticker(ticker)
    print(snap.to_json())


if __name__ == "__main__":
    main()
