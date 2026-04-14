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

The user tracks investments in a Notion database with columns:
**Ticker**, **Buy Price**, **Shares/Quantity**, **Date**, **Notes**.

When the user says "sync my positions from Notion":

1. Use the `notion` skill to query the user's investment database
2. For each row, extract ticker, buy_price, shares, and date
3. Write each entry to positions.json:

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey/stockmonkey"
source .venv/bin/activate
python -c "from app.positions import add_position; add_position('TICKER', BUY_PRICE, SHARES, 'YYYY-MM-DD', 'notion')"
```

Set the source to `"notion"` so synced entries are distinguishable from
manual entries. Repeat for each row in the Notion database.

The sync can also run automatically before the daily brief by adding it to
the cron job message.

## Dashboard Data

The pipeline automatically writes `docs/dashboard/data/latest.json` which
the web dashboard reads. After running the pipeline, commit and push the
updated `latest.json` so the dashboard reflects the latest data:

```bash
cd "/Users/sameerhassen/Desktop/TECH CAREER/Mil by 30/StockMonkey"
git add docs/data/latest.json stockmonkey/docs/dashboard/data/latest.json
git commit -m "update dashboard data"
git push origin main
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
- The script prints the full digest to stdout even if some tickers had errors

## Artifacts

Saved to `data/digests/` after each run:
- `YYYY-MM-DD_watchlist_digest.json` — structured data
- `YYYY-MM-DD_watchlist_digest.md` — formatted Markdown report
