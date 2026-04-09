"""Day-over-day snapshot comparison logic."""
from __future__ import annotations


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compare_snapshots(current: dict, previous: dict) -> dict:
    """Compare two snapshot dicts and return a structured comparison.

    Degrades gracefully if numeric fields are missing or malformed.
    """
    cur_price = _safe_float(current.get("price"))
    prev_price = _safe_float(previous.get("price"))

    if cur_price is not None and prev_price is not None:
        price_delta = round(cur_price - prev_price, 4)
        if price_delta > 0:
            direction = "up"
        elif price_delta < 0:
            direction = "down"
        else:
            direction = "flat"
    else:
        price_delta = None
        direction = "unknown"

    cur_headlines = current.get("headlines") or []
    prev_headlines = previous.get("headlines") or []
    headline_count_change = len(cur_headlines) - len(prev_headlines)
    prev_set = set(prev_headlines)
    new_headlines = [h for h in cur_headlines if h not in prev_set]

    if price_delta is not None:
        note = (
            f"Price moved {direction} by ${abs(price_delta):.2f} "
            f"since the last snapshot."
        )
    else:
        note = "Price comparison unavailable due to missing data."

    if new_headlines:
        note += f" {len(new_headlines)} new headline(s) detected."

    return {
        "previous_timestamp": previous.get("timestamp"),
        "price_delta": price_delta,
        "price_direction": direction,
        "headline_count_change": headline_count_change,
        "new_headlines_detected": len(new_headlines) > 0,
        "comparison_note": note,
    }
