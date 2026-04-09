"""Multi-ticker watchlist pipeline: extract → summarize → persist → compare → digest.

Usage:
    python -m app.run_watchlist AAPL NVDA TSLA
    python -m app.run_watchlist              # falls back to DEFAULT_TICKERS in .env
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from app.db.database import init_db
from app.db.repository import save_digest
from app.run_ticker_pipeline import run as run_single_ticker
from app.watchlist import load_tickers
from app.digest import build_digest


def run_watchlist(tickers: list[str]) -> dict:
    """Process every ticker and return the full watchlist result."""
    init_db()

    results: list[dict] = []
    for ticker in tickers:
        try:
            result = run_single_ticker(ticker)
        except Exception as exc:
            result = {
                "ticker": ticker,
                "snapshot": None,
                "llm_summary": None,
                "previous_snapshot": None,
                "comparison": None,
                "error": str(exc),
            }
        results.append(result)

    digest_summary = build_digest(results)

    now = datetime.now(timezone.utc)
    save_digest(
        digest_date=now.strftime("%Y-%m-%d"),
        watchlist=tickers,
        digest_summary=digest_summary,
    )

    return {
        "watchlist": tickers,
        "generated_at": now.isoformat(),
        "results": results,
        "digest_summary": digest_summary,
    }


def main() -> None:
    cli_args = sys.argv[1:] or None
    tickers = load_tickers(cli_args)

    if not tickers:
        print("No tickers provided. Pass them as arguments or set DEFAULT_TICKERS in .env")
        sys.exit(1)

    output = run_watchlist(tickers)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
