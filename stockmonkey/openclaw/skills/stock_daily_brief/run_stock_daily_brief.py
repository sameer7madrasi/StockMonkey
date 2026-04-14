"""OpenClaw skill entry point: generate and save a daily stock brief.

Usage (invoked by OpenClaw agent or manually):
    cd stockmonkey
    source .venv/bin/activate
    python openclaw/skills/stock_daily_brief/run_stock_daily_brief.py
    python openclaw/skills/stock_daily_brief/run_stock_daily_brief.py AAPL NVDA TSLA

Output goes to stdout (Markdown digest) and saved to data/digests/.
The OpenClaw agent handles delivery to Telegram via its native channel.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the stockmonkey project root is on sys.path so `app.*` imports work
# regardless of the working directory or how OpenClaw invokes the script.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.run_watchlist import run_watchlist  # noqa: E402
from app.watchlist import load_tickers       # noqa: E402
from app.format_digest import format_digest_markdown  # noqa: E402
from app.positions import load_positions     # noqa: E402
from app.db.database import get_connection   # noqa: E402

_DIGEST_DIR = _PROJECT_ROOT / "data" / "digests"
_DASHBOARD_DATA = _PROJECT_ROOT / "docs" / "dashboard" / "data"
_GHPAGES_DATA = _PROJECT_ROOT.parent / "docs" / "data"


def _get_price_history(ticker: str, days: int = 30) -> list[dict]:
    """Pull up to `days` daily closing prices from SQLite for sparkline charts."""
    try:
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT date(timestamp) AS dt, price
            FROM snapshots
            WHERE ticker = ? AND price != ''
            GROUP BY date(timestamp)
            ORDER BY dt DESC
            LIMIT ?
            """,
            (ticker.upper(), days),
        ).fetchall()
        conn.close()
        result = [{"date": r["dt"], "price": float(r["price"])} for r in rows]
        result.reverse()
        return result
    except Exception:
        return []


def _build_dashboard_data(digest: dict) -> dict:
    """Extract a compact summary for the web dashboard."""
    positions_list = load_positions()
    pos_map = {p["ticker"].upper(): p for p in positions_list}

    stocks = []
    for r in digest.get("results", []):
        snap = r.get("snapshot") or {}
        llm = r.get("llm_summary") or {}
        ticker = r.get("ticker", "???")
        entry: dict = {
            "ticker": ticker,
            "price": snap.get("price"),
            "change": snap.get("change"),
            "percent_change": snap.get("percent_change"),
            "summary": llm.get("summary"),
        }

        if ticker.upper() in pos_map:
            entry["position"] = pos_map[ticker.upper()]

        history = _get_price_history(ticker)
        if history:
            entry["history"] = history

        stocks.append(entry)

    stocks.sort(key=lambda s: (0 if s.get("position") else 1, s["ticker"]))

    return {
        "generated_at": digest.get("generated_at"),
        "stocks": stocks,
    }


_DASHBOARD_URL = "https://sameer7madrasi.github.io/StockMonkey/"


def _build_compact_message(digest: dict) -> str:
    """Build the short Telegram-friendly message with per-ticker lines."""
    lines = ["Yo what's good, here's how the stocks are looking:", ""]
    for r in digest.get("results", []):
        snap = r.get("snapshot") or {}
        ticker = r.get("ticker", "???")
        pct = snap.get("percent_change")
        price = snap.get("price")
        if pct is None or price is None:
            lines.append(f"• {ticker} — data unavailable")
            continue
        arrow = "▲" if pct >= 0 else "▼"
        sign = "+" if pct >= 0 else ""
        lines.append(f"• {ticker} {arrow} {sign}{pct:.2f}% · ${price:,.2f}")
    lines.append("")
    lines.append(f"Tap for details: {_DASHBOARD_URL}")
    return "\n".join(lines)


def _save_artifacts(digest: dict, date_str: str) -> tuple[Path, Path]:
    """Write JSON, Markdown, and dashboard artifacts. Returns (json_path, md_path)."""
    _DIGEST_DIR.mkdir(parents=True, exist_ok=True)

    json_path = _DIGEST_DIR / f"{date_str}_watchlist_digest.json"
    json_path.write_text(json.dumps(digest, indent=2), encoding="utf-8")

    md_path = _DIGEST_DIR / f"{date_str}_watchlist_digest.md"
    md_path.write_text(format_digest_markdown(digest), encoding="utf-8")

    dashboard_json = json.dumps(_build_dashboard_data(digest), indent=2)

    _DASHBOARD_DATA.mkdir(parents=True, exist_ok=True)
    (_DASHBOARD_DATA / "latest.json").write_text(dashboard_json, encoding="utf-8")

    _GHPAGES_DATA.mkdir(parents=True, exist_ok=True)
    (_GHPAGES_DATA / "latest.json").write_text(dashboard_json, encoding="utf-8")

    return json_path, md_path


def run_daily_brief(tickers: list[str] | None = None) -> str:
    """Execute the full daily brief pipeline and return a concise status string."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    resolved_tickers = tickers or load_tickers()
    if not resolved_tickers:
        msg = f"[{date_str}] No tickers configured. Set DEFAULT_TICKERS in .env or pass them as arguments."
        print(msg)
        return msg

    try:
        digest = run_watchlist(resolved_tickers)
    except Exception as exc:
        digest = {
            "watchlist": resolved_tickers,
            "generated_at": now.isoformat(),
            "results": [],
            "digest_summary": {
                "overall_summary": f"Pipeline failed: {exc}",
                "top_movers": [],
                "tickers_with_new_headlines": [],
                "tickers_needing_attention": resolved_tickers,
            },
        }

    json_path, md_path = _save_artifacts(digest, date_str)

    compact = _build_compact_message(digest)
    print(compact)
    return compact


def main() -> None:
    cli_args = sys.argv[1:] or None
    run_daily_brief(cli_args)


if __name__ == "__main__":
    main()
