# How StockMonkey Works

*Written April 9, 2026 — an explanation of the full system as built through Phase 5.*

---

## What is this thing?

It's called **StockMonkey**. It's a Python program that lives on this laptop. Every weekday morning, it:

1. Opens a hidden web browser (you never see it)
2. Goes to Yahoo Finance for each stock
3. Reads the price, how much it moved today, and the latest news headlines
4. Asks an AI (GPT) to write a short, honest summary of what happened
5. Saves everything to a little database so it can compare today vs. yesterday
6. Writes a nice report and saves it as a file

That's it. No trading. No buying or selling. No financial advice. Just a daily briefing, like a news digest for your watchlist.

---

## How is it organized?

Everything lives inside `stockmonkey/`. Think of it like floors in a building:

### `app/` — where the real code lives

- **`yahoo_finance.py`** — the "browser robot." It opens Yahoo Finance in a headless (invisible) Chromium browser using a tool called Playwright, reads the page, and pulls out the price, change, headlines, and market status. If something fails, it doesn't crash — it just notes the error and keeps going.

- **`models.py`** — defines what a "ticker snapshot" looks like. Think of it as a form with blank fields: ticker name, price, change, percent change, headlines, timestamp, errors. Every extraction fills out one of these forms.

- **`llm/summarize.py`** — the "AI brain." It takes a filled-out snapshot form, sends it to OpenAI's GPT, and asks for a 1–3 sentence summary, one thing to watch next, and a confidence level (high/medium/low). The AI is instructed to never make stuff up, never say "buy" or "sell," and to admit when data is thin.

- **`db/database.py`** and **`db/repository.py`** — the "memory." A tiny SQLite database (a single file at `data/stock_agent.db`) that stores every snapshot, every headline, and every AI summary. This is what lets the system say "yesterday NVDA was $180, today it's $184."

- **`compare.py`** — the "day-over-day diff." It looks at today's snapshot vs. the last one saved for the same ticker and computes: did the price go up, down, or stay flat? Are there new headlines? By how much did it move?

- **`run_ticker_pipeline.py`** — runs the full sequence for one ticker: extract, summarize, save, compare.

- **`watchlist.py`** — loads the list of tickers to check. You can pass them on the command line, or it reads `DEFAULT_TICKERS=AAPL,NVDA,TSLA` from the `.env` file.

- **`run_watchlist.py`** — runs the pipeline for every ticker on the watchlist, then builds a combined digest with top movers, new headlines, and an overall summary paragraph.

- **`digest.py`** — the logic that figures out which stocks moved the most, which have fresh news, and which need attention. Then asks the AI to write one paragraph summarizing the whole watchlist.

- **`format_digest.py`** — turns all that structured data into a nice, readable Markdown report.

### `openclaw/skills/stock_daily_brief/` — the automation wrapper

- **`run_stock_daily_brief.py`** — the button that runs everything. It calls the watchlist pipeline, saves a JSON file and a Markdown file to `data/digests/`, and prints a short status. This is what the scheduler calls every morning.

- **`SKILL.md`** — instructions for OpenClaw (the automation tool) explaining what this skill does and doesn't do.

### `scripts/` — smoke tests

Tests we ran to make sure Playwright and OpenAI were working before we built anything on top of them.

### `data/` — storage

Where the SQLite database and saved digest files live. Excluded from git so nothing sensitive gets uploaded.

### `logs/` — output

Where output gets saved when you want to keep a copy.

---

## How does a run actually work?

When the cron job fires at 7 AM on a weekday, here's the chain:

```
OpenClaw scheduler triggers
  → run_stock_daily_brief.py
    → loads tickers: [AAPL, NVDA, TSLA]
    → for each ticker:
        → Playwright opens Yahoo Finance, scrapes the page
        → Data gets packed into a snapshot dict
        → Snapshot sent to GPT for a summary
        → Snapshot + headlines + summary saved to SQLite
        → Previous snapshot fetched from DB
        → Comparison computed (price delta, new headlines)
    → All 3 results collected
    → Digest built (top movers, attention flags, overall summary)
    → Digest saved to SQLite
    → JSON artifact saved to data/digests/
    → Markdown artifact saved to data/digests/
    → Status printed
```

If Apple's page fails to load? NVDA and TSLA still get processed. The error gets logged in the result. Nothing crashes.

---

## What are the key files you'd actually touch?

- **`.env`** — your API key and watchlist live here. Change `DEFAULT_TICKERS` to watch different stocks.
- **`data/digests/*.md`** — your daily reports. Open them to read the brief.
- **`data/stock_agent.db`** — the database with all historical snapshots. Gets richer over time.

---

## What it does NOT do

- Does not trade stocks
- Does not tell you to buy or sell anything
- Does not manage a portfolio
- Does not send messages anywhere (yet)
- Does not make up reasons for why a stock moved

It's a research assistant, not a trading bot. It watches, summarizes, and remembers.
