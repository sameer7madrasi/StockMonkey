"""Data-access helpers for snapshots, headlines, and LLM summaries."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from app.db.database import get_connection


# ── inserts ──────────────────────────────────────────────────────────

def save_snapshot(snapshot_dict: dict) -> int:
    """Insert a snapshot row and return its id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO snapshots
                (ticker, price, change, percent_change,
                 market_status, timestamp, errors_json, raw_snapshot_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_dict["ticker"],
                str(snapshot_dict.get("price", "")),
                str(snapshot_dict.get("change", "")),
                str(snapshot_dict.get("percent_change", "")),
                snapshot_dict.get("market_status"),
                snapshot_dict.get("timestamp"),
                json.dumps(snapshot_dict.get("errors", [])),
                json.dumps(snapshot_dict),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def save_headlines(snapshot_id: int, headlines: list[str]) -> None:
    """Insert headline rows linked to a snapshot."""
    if not headlines:
        return
    conn = get_connection()
    try:
        conn.executemany(
            "INSERT INTO headlines (snapshot_id, title, url) VALUES (?, ?, ?)",
            [(snapshot_id, h, None) for h in headlines],
        )
        conn.commit()
    finally:
        conn.close()


def save_llm_summary(snapshot_id: int, summary: dict) -> int:
    """Insert an LLM summary row and return its id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO llm_summaries
                (snapshot_id, summary, attention_note, confidence, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                snapshot_id,
                summary.get("summary"),
                summary.get("attention_note"),
                summary.get("confidence"),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


# ── queries ──────────────────────────────────────────────────────────

def get_previous_snapshot(ticker: str, before_id: int) -> dict | None:
    """Return the most recent snapshot for *ticker* inserted before *before_id*.

    Returns the full snapshot dict (from raw_snapshot_json) or None.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT raw_snapshot_json
            FROM snapshots
            WHERE ticker = ? AND id < ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (ticker.upper(), before_id),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["raw_snapshot_json"])
    finally:
        conn.close()


def get_headlines(snapshot_id: int) -> list[str]:
    """Return headline titles for a given snapshot."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT title FROM headlines WHERE snapshot_id = ? ORDER BY id",
            (snapshot_id,),
        ).fetchall()
        return [r["title"] for r in rows]
    finally:
        conn.close()


def save_digest(
    digest_date: str,
    watchlist: list[str],
    digest_summary: dict,
) -> int:
    """Insert a daily digest row and return its id."""
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO daily_digests
                (digest_date, watchlist_json, digest_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                digest_date,
                json.dumps(watchlist),
                json.dumps(digest_summary),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
