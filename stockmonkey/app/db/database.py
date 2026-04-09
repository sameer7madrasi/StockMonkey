"""SQLite database initialization and connection management."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DB_PATH = _DB_DIR / "stock_agent.db"

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS snapshots (
    id                INTEGER PRIMARY KEY,
    ticker            TEXT    NOT NULL,
    price             TEXT,
    change            TEXT,
    percent_change    TEXT,
    market_status     TEXT,
    timestamp         TEXT,
    errors_json       TEXT,
    raw_snapshot_json  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS headlines (
    id          INTEGER PRIMARY KEY,
    snapshot_id INTEGER NOT NULL,
    title       TEXT    NOT NULL,
    url         TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
);

CREATE TABLE IF NOT EXISTS llm_summaries (
    id             INTEGER PRIMARY KEY,
    snapshot_id    INTEGER NOT NULL,
    summary        TEXT,
    attention_note TEXT,
    confidence     TEXT,
    created_at     TEXT    NOT NULL,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_ticker_ts
    ON snapshots(ticker, timestamp DESC);

CREATE TABLE IF NOT EXISTS daily_digests (
    id              INTEGER PRIMARY KEY,
    digest_date     TEXT    NOT NULL,
    watchlist_json  TEXT    NOT NULL,
    digest_json     TEXT    NOT NULL,
    created_at      TEXT    NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables and indexes if they don't already exist."""
    conn = get_connection()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
