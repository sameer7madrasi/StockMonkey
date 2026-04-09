# Skill: Stock Daily Brief

## Purpose

Generate a daily stock watchlist brief by running the local StockMonkey pipeline.
This skill extracts live ticker data via Playwright, summarizes each ticker with
the OpenAI Responses API, compares against previous snapshots in SQLite, and
produces a combined digest.

## What This Skill Does

1. Runs the multi-ticker watchlist pipeline (`app.run_watchlist`)
2. Saves a JSON artifact to `data/digests/YYYY-MM-DD_watchlist_digest.json`
3. Saves a Markdown artifact to `data/digests/YYYY-MM-DD_watchlist_digest.md`
4. Returns a concise text summary suitable for agent output

## What This Skill Does NOT Do

- Does NOT place trades or execute orders
- Does NOT provide financial advice
- Does NOT use words like buy, sell, hold, bullish, or bearish
- Does NOT browse the web freely — it only uses the local Playwright extractor
- Does NOT hallucinate or invent causes for price movements

## How to Use

Run the skill script directly:

```bash
cd stockmonkey
python openclaw/skills/stock_daily_brief/run_stock_daily_brief.py
```

Or with explicit tickers:

```bash
python openclaw/skills/stock_daily_brief/run_stock_daily_brief.py AAPL NVDA TSLA
```

If no tickers are passed, the skill falls back to `DEFAULT_TICKERS` in `.env`.

## Scheduling via OpenClaw Cron

To run this skill every weekday morning at 7:00 AM Pacific:

```bash
openclaw cron add \
  --name "daily-stock-brief" \
  --cron "0 7 * * 1-5" \
  --tz "America/Los_Angeles" \
  --message "python openclaw/skills/stock_daily_brief/run_stock_daily_brief.py"
```

## Error Handling

- If one ticker fails, the rest continue processing
- If the entire pipeline fails, a minimal error artifact is still saved
- Partial results are always preserved rather than discarded
