---
name: stock-daily-brief
description: Generate daily stock watchlist briefs and manage a personal ticker watchlist using the StockMonkey pipeline.
---

# Skill: StockMonkey — Daily Stock Brief & Watchlist Manager

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

## Output Format

The brief produces Markdown with these sections:
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
