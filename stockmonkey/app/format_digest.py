"""Convert a structured watchlist digest dict into a Markdown report."""
from __future__ import annotations


def _safe(val, fallback: str = "N/A") -> str:
    return str(val) if val is not None else fallback


def format_digest_markdown(digest: dict) -> str:
    """Return a human-readable Markdown string from a watchlist digest dict."""
    lines: list[str] = []
    date = digest.get("generated_at", "unknown")[:10]

    lines.append(f"# Daily Stock Brief — {date}")
    lines.append("")

    # ── overall summary ──────────────────────────────────────────────
    ds = digest.get("digest_summary") or {}
    lines.append("## Overall Summary")
    lines.append("")
    lines.append(ds.get("overall_summary", "No overall summary available."))
    lines.append("")

    # ── top movers ───────────────────────────────────────────────────
    movers = ds.get("top_movers") or []
    if movers:
        lines.append("## Top Movers")
        lines.append("")
        for m in movers:
            pct = _safe(m.get("percent_change"))
            price = _safe(m.get("price"))
            lines.append(f"- **{m['ticker']}**: {pct}% (${price})")
        lines.append("")

    # ── new headlines ────────────────────────────────────────────────
    new_hl = ds.get("tickers_with_new_headlines") or []
    if new_hl:
        lines.append("## Tickers With New Headlines")
        lines.append("")
        for t in new_hl:
            lines.append(f"- {t}")
        lines.append("")

    # ── needing attention ────────────────────────────────────────────
    attn = ds.get("tickers_needing_attention") or []
    if attn:
        lines.append("## Tickers Needing Attention")
        lines.append("")
        for t in attn:
            lines.append(f"- {t}")
        lines.append("")

    # ── per-ticker detail ────────────────────────────────────────────
    results = digest.get("results") or []
    if results:
        lines.append("---")
        lines.append("")
        lines.append("## Per-Ticker Detail")
        lines.append("")

    for r in results:
        ticker = r.get("ticker", "???")
        lines.append(f"### {ticker}")
        lines.append("")

        snap = r.get("snapshot") or {}
        error = r.get("error")

        if error:
            lines.append(f"> **Pipeline error:** {error}")
            lines.append("")
            continue

        price = _safe(snap.get("price"))
        change = _safe(snap.get("change"))
        pct = _safe(snap.get("percent_change"))
        status = _safe(snap.get("market_status"))
        lines.append(f"**Price:** ${price}  |  **Change:** {change} ({pct}%)  |  {status}")
        lines.append("")

        llm = r.get("llm_summary") or {}
        if llm.get("summary"):
            lines.append(f"**Summary:** {llm['summary']}")
            lines.append("")
        if llm.get("attention_note"):
            lines.append(f"**Watch:** {llm['attention_note']}")
            lines.append("")
        if llm.get("confidence"):
            lines.append(f"**Confidence:** {llm['confidence']}")
            lines.append("")

        comp = r.get("comparison")
        if comp:
            lines.append(f"**vs. Previous:** {comp.get('comparison_note', 'N/A')}")
            lines.append("")

        snap_errors = snap.get("errors") or []
        if snap_errors:
            lines.append(f"**Extraction errors:** {', '.join(snap_errors)}")
            lines.append("")

    # ── footer ───────────────────────────────────────────────────────
    lines.append("---")
    lines.append(f"*Generated at {digest.get('generated_at', 'unknown')}*")
    lines.append("")

    return "\n".join(lines)
