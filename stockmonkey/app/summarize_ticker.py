"""CLI entry point: extract a ticker snapshot and summarize it via LLM.

Usage:
    python -m app.summarize_ticker NVDA
"""
from __future__ import annotations

import json
import sys

from app.yahoo_finance import extract_ticker
from app.llm.summarize import summarize_snapshot


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    snap = extract_ticker(ticker)
    snapshot_dict = snap.to_dict()

    llm_summary = summarize_snapshot(snapshot_dict)

    output = {
        "ticker": ticker.upper(),
        "snapshot": snapshot_dict,
        "llm_summary": llm_summary,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
