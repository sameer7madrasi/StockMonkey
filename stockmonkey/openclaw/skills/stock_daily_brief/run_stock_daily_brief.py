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
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from app.notion_sync import sync_from_notion # noqa: E402
from app.yahoo_history import fetch_history  # noqa: E402

try:
    from dotenv import load_dotenv  # noqa: E402

    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

_DIGEST_DIR = _PROJECT_ROOT / "data" / "digests"
_DASHBOARD_DATA = _PROJECT_ROOT / "docs" / "dashboard" / "data"
_GHPAGES_DATA = _PROJECT_ROOT.parent / "docs" / "data"


def _sync_positions_quietly() -> None:
    """Attempt to sync positions from Notion; swallow errors so the pipeline continues."""
    try:
        sync_from_notion()
    except Exception:
        pass


def _build_dashboard_data(digest: dict) -> dict:
    """Extract a compact summary for the web dashboard."""
    _sync_positions_quietly()
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


def _save_history_files(tickers: list[str]) -> None:
    """Fetch Yahoo Finance chart data for each ticker and write per-ticker history JSON."""
    local_dir = _DASHBOARD_DATA / "history"
    ghpages_dir = _GHPAGES_DATA / "history"
    local_dir.mkdir(parents=True, exist_ok=True)
    ghpages_dir.mkdir(parents=True, exist_ok=True)

    def _one(ticker: str) -> tuple[str, dict | None]:
        try:
            return ticker.upper(), fetch_history(ticker)
        except Exception:
            return ticker.upper(), None

    workers = min(6, max(1, len(tickers)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_one, t): t for t in tickers}
        for fut in as_completed(futures):
            sym, history = fut.result()
            if not history:
                continue
            payload = json.dumps(history)
            (local_dir / f"{sym}.json").write_text(payload, encoding="utf-8")
            (ghpages_dir / f"{sym}.json").write_text(payload, encoding="utf-8")


def _sync_dashboard_html_to_pages() -> None:
    """Keep repo-root docs/index.html in sync with the canonical dashboard HTML."""
    src = _PROJECT_ROOT / "docs" / "dashboard" / "index.html"
    dst = _GHPAGES_DATA.parent / "index.html"
    if src.exists():
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _auto_push_enabled() -> bool:
    v = os.getenv("STOCKMONKEY_AUTO_PUSH", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _maybe_git_push_dashboard() -> None:
    """If STOCKMONKEY_AUTO_PUSH is set, commit and push dashboard artifacts to origin."""
    if not _auto_push_enabled():
        return

    repo = _PROJECT_ROOT.parent
    branch = (os.getenv("STOCKMONKEY_GIT_BRANCH") or "main").strip() or "main"

    paths = [
        "docs/data/latest.json",
        "docs/data/history",
        "docs/index.html",
        "stockmonkey/docs/dashboard/data/latest.json",
        "stockmonkey/docs/dashboard/data/history",
        "stockmonkey/docs/dashboard/index.html",
    ]

    try:
        add = subprocess.run(
            ["git", "-C", str(repo), "add", "--"] + paths,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if add.returncode != 0:
            print(f"[auto-push] git add failed: {add.stderr or add.stdout}", file=sys.stderr)
            return

        diff = subprocess.run(
            ["git", "-C", str(repo), "diff", "--staged", "--quiet"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if diff.returncode == 0:
            return

        msg = (
            "chore: refresh dashboard data "
            + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        )
        commit = subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", msg],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if commit.returncode != 0:
            print(f"[auto-push] git commit failed: {commit.stderr or commit.stdout}", file=sys.stderr)
            return

        push = subprocess.run(
            ["git", "-C", str(repo), "push", "origin", branch],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if push.returncode != 0:
            print(f"[auto-push] git push failed: {push.stderr or push.stdout}", file=sys.stderr)
        else:
            print(f"[auto-push] pushed to origin/{branch}")
    except subprocess.TimeoutExpired:
        print("[auto-push] git operation timed out", file=sys.stderr)
    except FileNotFoundError:
        print("[auto-push] git not found on PATH", file=sys.stderr)


def _save_artifacts(digest: dict, date_str: str) -> tuple[Path, Path]:
    """Write JSON, Markdown, dashboard, and history artifacts. Returns (json_path, md_path)."""
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

    all_tickers = [r.get("ticker", "") for r in digest.get("results", []) if r.get("ticker")]
    _save_history_files(all_tickers)
    _sync_dashboard_html_to_pages()
    _maybe_git_push_dashboard()

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
