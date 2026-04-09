"""Full pipeline: extract → summarize → persist → compare.

Usage:
    python -m app.run_ticker_pipeline NVDA
"""
from __future__ import annotations

import json
import sys

from app.yahoo_finance import extract_ticker
from app.llm.summarize import summarize_snapshot
from app.db.database import init_db
from app.db.repository import (
    save_snapshot,
    save_headlines,
    save_llm_summary,
    get_previous_snapshot,
)
from app.compare import compare_snapshots


def run(ticker: str) -> dict:
    """Execute the full pipeline for a single ticker and return the result."""
    init_db()

    snap = extract_ticker(ticker)
    snapshot_dict = snap.to_dict()

    llm_summary = summarize_snapshot(snapshot_dict)

    snapshot_id = save_snapshot(snapshot_dict)
    save_headlines(snapshot_id, snapshot_dict.get("headlines", []))
    save_llm_summary(snapshot_id, llm_summary)

    prev = get_previous_snapshot(ticker, before_id=snapshot_id)
    comparison = compare_snapshots(snapshot_dict, prev) if prev else None

    return {
        "ticker": ticker.upper(),
        "snapshot": snapshot_dict,
        "llm_summary": llm_summary,
        "previous_snapshot": prev,
        "comparison": comparison,
    }


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = run(ticker)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
