"""Sync investment positions from a Notion database into positions.json.

Reads the user's 'Investments' database via the Notion API and writes
each active stock position to data/positions.json. Non-stock asset types
and non-active positions are skipped.

The Notion API key is read from ~/.openclaw/openclaw.json at
skills.entries.notion.apiKey.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

from app.positions import add_position, load_positions

_OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"
_NOTION_DB_ID = "835bb889-e405-4856-8344-f71bd2da3bad"
_NOTION_VERSION = "2022-06-28"

_TICKER_RE = re.compile(r"^([A-Z]{1,5})\b")


def _get_api_key() -> str:
    config = json.loads(_OPENCLAW_CONFIG.read_text(encoding="utf-8"))
    key = config.get("skills", {}).get("entries", {}).get("notion", {}).get("apiKey")
    if not key:
        raise RuntimeError("Notion API key not configured in openclaw.json")
    return key


def _extract_ticker(title_text: str) -> str | None:
    """Extract the ticker symbol from strings like 'RACE (Ferrari)' or 'CL (Colgate-Palmolive)'."""
    m = _TICKER_RE.match(title_text.strip())
    return m.group(1) if m else None


def _query_database(api_key: str) -> list[dict]:
    """Fetch all pages from the Investments Notion database."""
    pages: list[dict] = []
    payload: dict = {}
    while True:
        req = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{_NOTION_DB_ID}/query",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": _NOTION_VERSION,
                "Content-Type": "application/json",
            },
        )
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return pages


def sync_from_notion() -> list[dict]:
    """Pull positions from Notion and write them to positions.json.

    Returns the final list of synced positions.
    """
    api_key = _get_api_key()
    pages = _query_database(api_key)

    synced = 0
    for page in pages:
        props = page.get("properties", {})

        status_sel = (props.get("Status") or {}).get("select") or {}
        if status_sel.get("name", "").lower() != "active":
            continue

        asset_sel = (props.get("Asset Type") or {}).get("select") or {}
        if "stock" not in asset_sel.get("name", "").lower():
            continue

        title_parts = (props.get("Investment") or {}).get("title", [])
        title_text = "".join(t.get("plain_text", "") for t in title_parts)
        ticker = _extract_ticker(title_text)
        if not ticker:
            continue

        buy_price = (props.get("Price In") or {}).get("number")
        shares = (props.get("Number of Shares") or {}).get("number", 1)
        date_obj = (props.get("Date Invested") or {}).get("date") or {}
        buy_date = date_obj.get("start", "")

        if buy_price is None:
            continue

        add_position(ticker, float(buy_price), float(shares), buy_date, "notion")
        synced += 1

    positions = load_positions()
    print(f"Synced {synced} positions from Notion. Total: {len(positions)}")
    return positions


if __name__ == "__main__":
    sync_from_notion()
