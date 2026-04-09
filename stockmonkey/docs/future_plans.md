# StockMonkey — Future Plans

*Captured April 9, 2026 after completing the core pipeline + Telegram delivery.*

---

### 1. Move off the laptop

Deploy to a $4/month VPS (DigitalOcean, Railway, Fly.io) so the pipeline runs every morning regardless of whether the laptop is open, closed, or on a plane. The code is already self-contained — it's just a deployment step.

### 2. Add a 30-day retention cleanup

One SQL query at the end of each pipeline run to delete snapshots older than 30 days. Keeps the database lean forever. Not urgent (growth is ~2 MB/year) but good hygiene.

### 3. Scrape richer data from Yahoo Finance

The quote page has previous close, open, day range, 52-week range, volume, and market cap sitting in the statistics panel. Scraping these would make comparisons richer and AI summaries sharper without needing the database for basic context.

### 4. Make the summaries more actionable

With richer data and a refined prompt, the AI could say things like "AAPL is 8% below its 52-week high, volume was 20% above average, and 3 of 5 headlines mention AI regulation." Still no advice — just more useful as a daily nudge.

### 5. Weekly recap digest

Every Friday or Sunday, pull the week's snapshots from SQLite, compute weekly change per ticker, and send a "this week in your watchlist" summary. The infrastructure is already there — it's just a new query + prompt.

### 6. Expand Telegram bot commands

Beyond `stonks`, add:
- `add MSFT` — add a ticker to the watchlist
- `remove TSLA` — remove one
- `watchlist` — show current tickers
- `history NVDA` — show last 5 snapshots for a ticker

All trivial with the SQLite layer already in place.

### 7. Alerts for big moves

Instead of waiting to be asked, check midday for any ticker that moved more than 3–5% and proactively send a Telegram message. Turns the system from a morning digest into a real-time watchdog.

### 8. Track actual portfolio positions

If holding specific positions, track cost basis and report how holdings are performing: "NVDA is up 1% today, you're up 47% since your entry at $125." Still not advice — just awareness.
