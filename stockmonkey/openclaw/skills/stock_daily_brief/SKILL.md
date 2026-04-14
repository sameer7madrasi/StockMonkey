---
name: stock-daily-brief
description: Generate daily stock watchlist briefs and manage a personal ticker watchlist using the StockMonkey pipeline.
---

# Skill: StockMonkey — Daily Stock Brief & Watchlist Manager

## CRITICAL — Telegram Message Format

When replying with stock data via Telegram — whether from a cron job OR an
on-demand request from the user — you MUST send ONLY this compact format.
Do NOT send the full Markdown digest. Do NOT send long paragraphs.
Do NOT include summaries, headlines, or per-ticker detail in the message.

The ONLY message the user should receive is:

```
Yo what's good, here's how the stocks are looking:

• TICKER1 ▲ +X.XX% · $PRICE
• TICKER2 ▼ -X.XX% · $PRICE
• TICKER3 ▼ -X.XX% · $PRICE

Tap for details: https://sameer7madrasi.github.io/StockMonkey/
```

Use ▲ for stocks that are up and ▼ for stocks that are down.
Include the percent change and current price for each ticker.
Always end with the dashboard link. That is the ENTIRE message. Nothing else.

## Purpose

Generate daily stock watchlist briefs and manage a personal ticker watchlist.
This skill extracts live ticker data from Yahoo Finance via Playwright,
summarizes each ticker with the OpenAI Responses API, compares against
previous snapshots in SQLite, and produces a combined digest with
programmatic analysis and an LLM-generated summary.

## Trigger Phrases

- "stock brief", "stonks", "run my stocks", "daily brief"
- "watchlist", "show my watchlist", "what am I watching"
- "add TICKER", "track TICKER", "start watching TICKER"
- "remove TICKER", "stop watching TICKER", "drop TICKER"
- "how is TICKER doing", "check TICKER"
- "I bought X shares of TICKER at $PRICE"
- "I sold TICKER", "remove my TICKER position"
- "show my positions", "what am I invested in"
- "sync my positions from Notion", "sync Notion"

## Project Location

```
PROJECT_ROOT=/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey
VENV=$PROJECT_ROOT/.venv
```

All commands must be run from `$PROJECT_ROOT` with the venv activated.

## Commands

### Run a Full Stock Brief

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey"
source .venv/bin/activate
python openclaw/skills/stock_daily_brief/run_stock_daily_brief.py
```

This processes every ticker on the watchlist and prints a Markdown digest
to stdout. Artifacts are also saved to `data/digests/`.

To run for specific tickers (overriding the watchlist):

```bash
python openclaw/skills/stock_daily_brief/run_stock_daily_brief.py AAPL NVDA TSLA
```

### Show Current Watchlist

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey"
source .venv/bin/activate
python -c "from app.watchlist import load_tickers; print('\n'.join(load_tickers()) or 'Watchlist is empty')"
```

### Add a Ticker

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey"
source .venv/bin/activate
python -c "from app.watchlist import add_ticker; added, tickers = add_ticker('TICKER'); print(f'Added: {added}. Watchlist: {tickers}')"
```

Replace `TICKER` with the actual ticker symbol (e.g. `AAPL`).

### Remove a Ticker

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey"
source .venv/bin/activate
python -c "from app.watchlist import remove_ticker; removed, tickers = remove_ticker('TICKER'); print(f'Removed: {removed}. Watchlist: {tickers}')"
```

## Position Management

Users can tell you about stocks they own. Handle these commands:

### Record a Purchase

When the user says something like "I bought 5 shares of AAPL at $180" or
"yo I just bought COST at $950, 2 shares":

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey"
source .venv/bin/activate
python -c "from app.positions import add_position; new, pos = add_position('TICKER', BUY_PRICE, SHARES, 'YYYY-MM-DD'); print(f'New: {new}. Positions: {pos}')"
```

Replace TICKER, BUY_PRICE, SHARES, and date with actual values. If shares
are not mentioned, default to 1. If date is not mentioned, use today's date.

### Record a Sale

When the user says "I sold AAPL" or "remove my COST position":

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey"
source .venv/bin/activate
python -c "from app.positions import remove_position; removed, pos = remove_position('TICKER'); print(f'Removed: {removed}. Positions: {pos}')"
```

### Show Positions

When the user asks "show my positions" or "what am I invested in":

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey"
source .venv/bin/activate
python -c "from app.positions import load_positions; ps = load_positions(); print('\n'.join(f\"{p['ticker']}: {p['shares']} shares @ \${p['buy_price']}\" for p in ps) if ps else 'No positions recorded.')"
```

## Notion Sync

The user tracks investments in a Notion database (DB ID:
`835bb889-e405-4856-8344-f71bd2da3bad`) on a page called "Investments"
inside "Money Matters". The database columns are: Investment (title with
format "TICKER (Name)"), Price In, Number of Shares, Date Invested,
Asset Type, Status, Amount Invested, Platform / Custodian, Notes.

**Automatic sync:** The pipeline automatically syncs positions from Notion
every time the daily brief runs. No manual action is needed.

**On-demand sync:** When the user says "sync my positions from Notion":

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey"
source .venv/bin/activate
python -c "from app.notion_sync import sync_from_notion; sync_from_notion()"
```

Only rows with Status = "Active" and Asset Type containing "stock" are
synced. The ticker is extracted from the Investment title (e.g. "RACE
(Ferrari)" -> RACE). Synced entries have source = "notion" in
positions.json.

## Dashboard Data & GitHub Pages

The pipeline writes dashboard JSON and Yahoo history files under
`docs/data/` (GitHub Pages) and mirrors under `stockmonkey/docs/dashboard/data/`.
It also copies `stockmonkey/docs/dashboard/index.html` to `docs/index.html`.

### Auto-push (recommended)

So Telegram and the live dashboard stay in sync, set in `stockmonkey/.env`:

```
STOCKMONKEY_AUTO_PUSH=1
```

Optional: `STOCKMONKEY_GIT_BRANCH=main` (default).

After each successful run the script commits and pushes those paths if there
are changes. Requires `git` on PATH, repo credentials (SSH or credential
helper), and permission to push to `origin`.

### Manual push

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey"
git add docs/data/latest.json docs/data/history docs/index.html \
  stockmonkey/docs/dashboard/data/latest.json stockmonkey/docs/dashboard/data/history \
  stockmonkey/docs/dashboard/index.html
git commit -m "update dashboard data"
git push origin main
```

## Cron reliability (OpenClaw)

The scheduled job runs on the **same Mac** where the OpenClaw gateway is
running. If the laptop is **off or asleep** at 7am, the job may not run or
may **time out** waiting for the machine or network.

- **Reduce timeouts / noise:** Prefer a longer `--timeout-seconds` on the
  cron job (e.g. 1200). Use `--failure-alert-after 3` and
  `--failure-alert-cooldown 8h` so Telegram is not spammed on transient
  misses. Use `--no-failure-alert` if you only want logs
  (`openclaw cron runs`) and no automatic error DMs.
- **Catch up after login:** Install the optional LaunchAgent
  `stockmonkey/scripts/ai.stockmonkey.catchup-on-login.plist` into
  `~/Library/LaunchAgents/` and `launchctl load` it — it runs
  `scripts/catchup_on_login.sh` once per login with `STOCKMONKEY_AUTO_PUSH=1`
  so a missed morning run refreshes the dashboard when you open the machine.

```bash
cp "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey/scripts/ai.stockmonkey.catchup-on-login.plist" ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/ai.stockmonkey.catchup-on-login.plist
```

## Full Output Format

The full Markdown digest (saved to artifacts) contains these sections:
- **Overall Summary** — LLM-generated narrative
- **Top Movers** — tickers with largest price swings
- **Tickers With New Headlines** — tickers that have fresh news
- **Tickers Needing Attention** — tickers flagged for closer inspection
- **Per-Ticker Detail** — price, change, LLM summary, day-over-day comparison

## What This Skill Does NOT Do

- Does NOT place trades or execute orders
- Does NOT provide financial advice
- Does NOT use words like buy, sell, hold, bullish, or bearish
- Does NOT hallucinate or invent causes for price movements

## Error Handling

- If one ticker fails, the rest continue processing
- Partial results are always preserved rather than discarded
- The script prints the compact Telegram message to stdout (and saves the full
  digest under `data/digests/`) even if some tickers had errors

## Artifacts

Saved to `data/digests/` after each run:
- `YYYY-MM-DD_watchlist_digest.json` — structured data
- `YYYY-MM-DD_watchlist_digest.md` — formatted Markdown report
