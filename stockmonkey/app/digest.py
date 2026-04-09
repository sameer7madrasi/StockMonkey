"""Watchlist digest: programmatic analysis + LLM overall summary."""
from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_MODEL = os.getenv("OPENCLAW_MODEL", "gpt-5.4")

_LARGE_MOVE_THRESHOLD = 2.0  # percent

_DIGEST_INSTRUCTIONS = """\
You are a concise daily-digest summarizer for a retail investor's stock watchlist.

Rules you MUST follow:
- Base your summary ONLY on the structured result objects provided.
- Do NOT give financial advice. Never use words like buy, sell, hold, \
bullish, or bearish.
- Do NOT invent causes for price movements or fabricate details.
- If data is sparse, mixed quality, or contains errors, say so plainly.
- Keep language plain, direct, and under 100 words.

Return ONLY a single plain-text paragraph (no JSON, no markdown).\
"""


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ── programmatic helpers ─────────────────────────────────────────────

def _top_movers(results: list[dict], n: int = 3) -> list[dict]:
    """Return up to *n* tickers sorted by largest absolute percent change."""
    scored: list[tuple[float, dict]] = []
    for r in results:
        pct = _safe_float(r.get("snapshot", {}).get("percent_change"))
        if pct is not None:
            scored.append((abs(pct), {
                "ticker": r["ticker"],
                "percent_change": pct,
                "price": r["snapshot"].get("price"),
            }))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored[:n]]


def _tickers_with_new_headlines(results: list[dict]) -> list[str]:
    tickers: list[str] = []
    for r in results:
        comp = r.get("comparison") or {}
        if comp.get("new_headlines_detected"):
            tickers.append(r["ticker"])
    return tickers


def _tickers_needing_attention(results: list[dict]) -> list[str]:
    """Conservative rule-based flagging."""
    tickers: list[str] = []
    for r in results:
        dominated_by = set()

        pct = _safe_float(r.get("snapshot", {}).get("percent_change"))
        if pct is not None and abs(pct) >= _LARGE_MOVE_THRESHOLD:
            dominated_by.add("large_move")

        comp = r.get("comparison") or {}
        if comp.get("new_headlines_detected"):
            dominated_by.add("new_headlines")

        if r.get("llm_summary", {}).get("confidence") == "low":
            dominated_by.add("low_confidence")

        if r.get("snapshot", {}).get("errors"):
            dominated_by.add("extraction_errors")

        if dominated_by:
            tickers.append(r["ticker"])

    return tickers


# ── LLM overall summary ─────────────────────────────────────────────

def _generate_overall_summary(results: list[dict]) -> str:
    """Ask the LLM for a short paragraph summarizing the full watchlist."""
    condensed = []
    for r in results:
        entry = {
            "ticker": r["ticker"],
            "price": r.get("snapshot", {}).get("price"),
            "percent_change": r.get("snapshot", {}).get("percent_change"),
            "market_status": r.get("snapshot", {}).get("market_status"),
            "headline_count": len(r.get("snapshot", {}).get("headlines", [])),
            "llm_confidence": r.get("llm_summary", {}).get("confidence"),
            "comparison_note": (r.get("comparison") or {}).get("comparison_note"),
        }
        condensed.append(entry)

    try:
        response = _client.responses.create(
            model=_MODEL,
            instructions=_DIGEST_INSTRUCTIONS,
            input=json.dumps(condensed, indent=2),
        )
        return response.output_text.strip()
    except Exception as exc:
        return f"Digest summary unavailable: {exc}"


# ── public API ───────────────────────────────────────────────────────

def build_digest(results: list[dict]) -> dict:
    """Build the digest_summary object from a list of per-ticker results."""
    return {
        "overall_summary": _generate_overall_summary(results),
        "top_movers": _top_movers(results),
        "tickers_with_new_headlines": _tickers_with_new_headlines(results),
        "tickers_needing_attention": _tickers_needing_attention(results),
    }
