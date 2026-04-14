"""Fetch historical price data from Yahoo Finance's v8 chart API.

This uses the same API endpoint that powers Yahoo Finance's own charts,
so the data is identical to what you see on their website.
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone

_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

_RANGES: list[tuple[str, dict[str, str]]] = [
    ("1D",  {"range": "1d",  "interval": "5m"}),
    ("5D",  {"range": "5d",  "interval": "15m"}),
    ("1M",  {"range": "1mo", "interval": "1d"}),
    ("6M",  {"range": "6mo", "interval": "1d"}),
    ("1Y",  {"range": "1y",  "interval": "1d"}),
    ("YTD", {"interval": "1d"}),
    ("5Y",  {"range": "5y",  "interval": "1wk"}),
    ("Max", {"range": "max", "interval": "1mo"}),
]


def _ytd_period1() -> int:
    """Unix timestamp for Jan 1 of the current year."""
    jan1 = datetime(datetime.now(timezone.utc).year, 1, 1, tzinfo=timezone.utc)
    return int(jan1.timestamp())


def _fetch_range(symbol: str, params: dict[str, str], range_key: str) -> list[dict]:
    """Fetch one time range from Yahoo and return a list of {date, price} dicts."""
    qs_parts = [f"{k}={v}" for k, v in params.items()]

    if range_key == "YTD":
        qs_parts.append(f"period1={_ytd_period1()}")
        qs_parts.append(f"period2={int(time.time())}")

    url = _BASE_URL.format(symbol=symbol) + "?" + "&".join(qs_parts)

    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    })

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
    except Exception:
        return []

    result_list = data.get("chart", {}).get("result")
    if not result_list:
        return []

    result = result_list[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators", {})

    adjclose_list = indicators.get("adjclose", [{}])
    adjclose_vals = adjclose_list[0].get("adjclose") if adjclose_list else None

    quote_list = indicators.get("quote", [{}])
    close_vals = quote_list[0].get("close") if quote_list else None

    prices = adjclose_vals or close_vals
    if not prices or not timestamps:
        return []

    is_intraday = params.get("interval", "1d") in ("1m", "5m", "15m", "30m", "60m", "90m", "1h")

    points = []
    for ts, price in zip(timestamps, prices):
        if price is None:
            continue
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        if is_intraday:
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        else:
            date_str = dt.strftime("%Y-%m-%d")
        points.append({"date": date_str, "price": round(price, 2)})

    return points


def fetch_history(symbol: str) -> dict[str, list[dict]]:
    """Fetch all 8 time ranges for a ticker. Returns a dict keyed by range label."""
    symbol = symbol.strip().upper()
    history: dict[str, list[dict]] = {}

    for range_key, params in _RANGES:
        history[range_key] = _fetch_range(symbol, params, range_key)

    return history


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    h = fetch_history(ticker)
    for k, v in h.items():
        print(f"{k}: {len(v)} points", f"({v[0]['date']} to {v[-1]['date']})" if v else "(empty)")
