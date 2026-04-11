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

_DIGEST_DIR = _PROJECT_ROOT / "data" / "digests"


def _save_artifacts(digest: dict, date_str: str) -> tuple[Path, Path]:
    """Write JSON and Markdown artifacts. Returns (json_path, md_path)."""
    _DIGEST_DIR.mkdir(parents=True, exist_ok=True)

    json_path = _DIGEST_DIR / f"{date_str}_watchlist_digest.json"
    json_path.write_text(json.dumps(digest, indent=2), encoding="utf-8")

    md_path = _DIGEST_DIR / f"{date_str}_watchlist_digest.md"
    md_path.write_text(format_digest_markdown(digest), encoding="utf-8")

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

    md_text = format_digest_markdown(digest)

    print(md_text)
    print(f"\n---\nArtifacts saved:\n  JSON: {json_path}\n  MD:   {md_path}")
    return md_text


def main() -> None:
    cli_args = sys.argv[1:] or None
    run_daily_brief(cli_args)


if __name__ == "__main__":
    main()
