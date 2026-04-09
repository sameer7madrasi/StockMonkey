"""LLM summarization layer for ticker snapshots using the OpenAI Responses API."""
from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

_MODEL = os.getenv("OPENCLAW_MODEL", "gpt-5.4")

SYSTEM_INSTRUCTIONS = """\
You are a concise stock-watchlist summarizer for retail investors.

Rules you MUST follow:
- Base your summary ONLY on the snapshot data provided. Never invent causes \
for price movements or fabricate details not present in the data.
- Do NOT give financial advice. Never use words like buy, sell, hold, \
bullish, or bearish.
- If the snapshot contains errors, missing fields, or sparse headlines, \
explicitly acknowledge the uncertainty in your summary and lower your \
confidence accordingly.
- Keep language plain, direct, and useful as a daily watchlist nudge.

Return ONLY valid JSON with exactly these three keys:
{
  "summary": "<1-3 sentences describing what happened based on the snapshot>",
  "attention_note": "<1 sentence on what the investor should watch next>",
  "confidence": "<exactly one of: high, medium, low>"
}

Do not wrap the JSON in markdown fences or add any text outside the JSON object.\
"""

_FALLBACK_SUMMARY = {
    "summary": "",
    "attention_note": "Review the raw snapshot manually.",
    "confidence": "low",
}


def summarize_snapshot(snapshot_dict: dict) -> dict:
    """Send a ticker snapshot to the LLM and return a structured summary.

    Returns a dict with keys: summary, attention_note, confidence.
    Falls back gracefully if the model returns invalid JSON.
    """
    user_content = json.dumps(snapshot_dict, indent=2)

    try:
        response = _client.responses.create(
            model=_MODEL,
            instructions=SYSTEM_INSTRUCTIONS,
            input=user_content,
        )
        raw = response.output_text.strip()
    except Exception as exc:
        fallback = _FALLBACK_SUMMARY.copy()
        fallback["summary"] = f"LLM call failed: {exc}"
        return fallback

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "summary": raw,
            "attention_note": "Review the raw snapshot manually.",
            "confidence": "low",
        }

    if parsed.get("confidence") not in ("high", "medium", "low"):
        parsed["confidence"] = "low"

    for key in ("summary", "attention_note", "confidence"):
        if key not in parsed:
            parsed[key] = _FALLBACK_SUMMARY[key]

    return parsed
