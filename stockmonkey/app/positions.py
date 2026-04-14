"""Investment position tracking: load, add, remove, and list positions.

Positions are stored in data/positions.json with this structure:
{
  "positions": [
    {"ticker": "COST", "buy_price": 950.0, "shares": 2, "buy_date": "2026-03-15", "source": "manual"}
  ]
}
"""
from __future__ import annotations

import json
from pathlib import Path

_POSITIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "positions.json"


def _read() -> list[dict]:
    if not _POSITIONS_PATH.exists():
        return []
    try:
        data = json.loads(_POSITIONS_PATH.read_text(encoding="utf-8"))
        return data.get("positions", [])
    except (json.JSONDecodeError, KeyError):
        return []


def _write(positions: list[dict]) -> None:
    _POSITIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _POSITIONS_PATH.write_text(
        json.dumps({"positions": positions}, indent=2) + "\n", encoding="utf-8"
    )


def load_positions() -> list[dict]:
    """Return all current positions."""
    return _read()


def get_position(ticker: str) -> dict | None:
    """Return the position for a specific ticker, or None."""
    ticker = ticker.strip().upper()
    for p in _read():
        if p.get("ticker", "").upper() == ticker:
            return p
    return None


def add_position(
    ticker: str,
    buy_price: float,
    shares: float = 1,
    buy_date: str = "",
    source: str = "manual",
) -> tuple[bool, list[dict]]:
    """Add or update a position. Returns (was_new, current_positions)."""
    ticker = ticker.strip().upper()
    positions = _read()

    for p in positions:
        if p.get("ticker", "").upper() == ticker:
            p["buy_price"] = buy_price
            p["shares"] = shares
            if buy_date:
                p["buy_date"] = buy_date
            p["source"] = source
            _write(positions)
            return False, positions

    positions.append({
        "ticker": ticker,
        "buy_price": buy_price,
        "shares": shares,
        "buy_date": buy_date,
        "source": source,
    })
    _write(positions)
    return True, positions


def remove_position(ticker: str) -> tuple[bool, list[dict]]:
    """Remove a position. Returns (was_removed, current_positions)."""
    ticker = ticker.strip().upper()
    positions = _read()
    original_len = len(positions)
    positions = [p for p in positions if p.get("ticker", "").upper() != ticker]
    _write(positions)
    return len(positions) < original_len, positions
