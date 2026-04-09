# Stock Agent Watchlist

## Setup

1. Install Node 24
2. Create Python venv
3. Install Python deps
4. Install Playwright browsers
5. Create `.env`

```bash
nvm install 24
python3 -m venv .venv
source .venv/bin/activate
pip install openai python-dotenv playwright
python -m playwright install chromium
cp .env.example .env
# Fill in your API keys in .env
```

## Commands

```bash
source .venv/bin/activate
python scripts/playwright_smoke_test.py
python scripts/openai_smoke_test.py
openclaw --help
```

## Project Structure

```
stockmonkey/
  app/          # Core application code
  scripts/      # Setup and smoke test scripts
  data/         # SQLite databases
  logs/         # Runtime logs
```
