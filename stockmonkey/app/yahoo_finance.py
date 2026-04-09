from __future__ import annotations

from playwright.sync_api import sync_playwright, Page, TimeoutError as PwTimeout

from app.models import TickerSnapshot

YAHOO_QUOTE_URL = "https://finance.yahoo.com/quote/{ticker}/"

SELECTORS = {
    "price": [
        '[data-testid="qsp-price"]',
        'fin-streamer[data-field="regularMarketPrice"]',
    ],
    "change": [
        '[data-testid="qsp-price-change"]',
        'fin-streamer[data-field="regularMarketChange"]',
    ],
    "percent_change": [
        '[data-testid="qsp-price-change-percent"]',
        'fin-streamer[data-field="regularMarketChangePercent"]',
    ],
    "market_status": [
        '[data-testid="price-statistic"] span.gap',
        '[data-testid="price-statistic"] span[class*="gap"]',
    ],
    "headlines": [
        '[data-testid="storyitem"] h3',
        '[data-testid="recent-news"] h3',
    ],
}

MAX_HEADLINES = 5


def _first_match_text(page: Page, candidates: list[str]) -> str | None:
    """Return inner text of the first selector that matches, or None."""
    for sel in candidates:
        try:
            el = page.query_selector(sel)
            if el:
                text = (el.inner_text() or "").strip()
                if text:
                    return text
        except PwTimeout:
            continue
    return None


def _parse_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    cleaned = raw.replace(",", "").replace("(", "").replace(")", "").replace("%", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_ticker(ticker: str, *, headless: bool = True) -> TickerSnapshot:
    """Launch a browser, scrape Yahoo Finance for *ticker*, return a snapshot."""
    ticker = ticker.upper().strip()
    snap = TickerSnapshot(ticker=ticker)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            url = YAHOO_QUOTE_URL.format(ticker=ticker)
            page.goto(url, wait_until="domcontentloaded", timeout=15_000)
            page.wait_for_timeout(3000)

            raw_price = _first_match_text(page, SELECTORS["price"])
            snap.price = _parse_float(raw_price)
            if snap.price is None:
                snap.errors.append("price not found")

            raw_change = _first_match_text(page, SELECTORS["change"])
            snap.change = _parse_float(raw_change)
            if snap.change is None:
                snap.errors.append("change not found")

            raw_pct = _first_match_text(page, SELECTORS["percent_change"])
            snap.percent_change = _parse_float(raw_pct)
            if snap.percent_change is None:
                snap.errors.append("percent_change not found")

            snap.market_status = _first_match_text(page, SELECTORS["market_status"])
            if snap.market_status is None:
                snap.errors.append("market_status not found")

            for sel in SELECTORS["headlines"]:
                els = page.query_selector_all(sel)
                if els:
                    for el in els[:MAX_HEADLINES]:
                        text = (el.inner_text() or "").strip()
                        if text:
                            snap.headlines.append(text)
                    break
            if not snap.headlines:
                snap.errors.append("headlines not found")

        except Exception as exc:
            snap.errors.append(f"extraction failed: {exc}")
        finally:
            browser.close()

    return snap
