"""Which OpenAI model the StockMonkey pipeline uses for summarization.

Resolution order (first wins):
  1. STOCKMONKEY_OPENAI_MODEL — use for this repo only (recommended: gpt-4o-mini)
  2. OPENCLAW_MODEL — legacy fallback when the pipeline shared the agent model
  3. gpt-4o-mini — cheap default so daily runs do not imply flagship pricing

OpenClaw's gateway/agent can keep OPENCLAW_MODEL for chat; set
STOCKMONKEY_OPENAI_MODEL in stockmonkey/.env to decouple billing.
"""
from __future__ import annotations

import os


def summary_model() -> str:
    for key in ("STOCKMONKEY_OPENAI_MODEL", "OPENCLAW_MODEL"):
        v = os.getenv(key)
        if v and str(v).strip():
            return str(v).strip()
    return "gpt-4o-mini"
