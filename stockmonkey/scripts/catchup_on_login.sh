#!/bin/zsh
# Run the daily brief once when you log in (LaunchAgent RunAtLoad).
# Catches up if the machine was asleep during the scheduled cron window.
# Set STOCKMONKEY_AUTO_PUSH=1 in the environment (or in ~/.zshrc) to push
# dashboard data to GitHub after a successful run.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STOCKMONKEY_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$STOCKMONKEY_ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

exec python openclaw/skills/stock_daily_brief/run_stock_daily_brief.py
