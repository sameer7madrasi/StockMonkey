"""Gate script: run the daily brief on first wake/login after market open.

Triggered by macOS LaunchAgent on login and wake-from-sleep.
Only runs the pipeline if ALL of these are true:
  1. Today is a weekday (Mon–Fri)
  2. Current time is after US market open (9:30 AM ET)
  3. Today's digest file does not already exist

Install the LaunchAgent:
  cp ai.stockmonkey.wake-trigger.plist ~/Library/LaunchAgents/
  launchctl load ~/Library/LaunchAgents/ai.stockmonkey.wake-trigger.plist
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_DIGEST_DIR = _PROJECT_ROOT / "data" / "digests"
_LOG_FILE = _PROJECT_ROOT / "logs" / "wake_trigger.log"

ET = ZoneInfo("America/New_York")
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30


def _log(msg: str) -> None:
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S %Z")
    line = f"[{ts}] {msg}\n"
    with open(_LOG_FILE, "a") as f:
        f.write(line)
    print(line, end="")


def _should_run() -> tuple[bool, str]:
    now_et = datetime.now(ET)

    if now_et.weekday() >= 5:
        return False, f"weekend ({now_et.strftime('%A')})"

    market_open = now_et.replace(
        hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0
    )
    if now_et < market_open:
        return False, f"before market open ({now_et.strftime('%H:%M')} ET < 09:30 ET)"

    date_str = now_et.strftime("%Y-%m-%d")
    digest_path = _DIGEST_DIR / f"{date_str}_watchlist_digest.json"
    if digest_path.exists():
        return False, f"already ran today ({digest_path.name} exists)"

    return True, "weekday, market open, no digest yet"


def main() -> None:
    should_run, reason = _should_run()

    if not should_run:
        _log(f"SKIP: {reason}")
        return

    _log(f"GO: {reason} — launching daily brief")

    from openclaw.skills.stock_daily_brief.run_stock_daily_brief import run_daily_brief

    try:
        result = run_daily_brief()
        _log(f"DONE: {result.splitlines()[0] if result else 'completed'}")
    except Exception as exc:
        _log(f"FAIL: {exc}")


if __name__ == "__main__":
    main()
