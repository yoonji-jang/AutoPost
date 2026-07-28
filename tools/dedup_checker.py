"""history_db/postings.db 대조로 중복 게시를 방지한다."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "history_db" / "postings.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mall TEXT NOT NULL,
            category TEXT NOT NULL,
            product_id TEXT NOT NULL,
            posted_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_mall_category ON postings(mall, category)"
    )
    return conn


def was_recently_posted(mall: str, category: str, product_id: str, within_days: int = 30) -> bool:
    """최근 N일 내 동일 (mall, category, product_id) 조합이 게시됐는지 확인한다."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=within_days)).isoformat()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM postings
            WHERE mall = ? AND category = ? AND product_id = ? AND posted_at >= ?
            LIMIT 1
            """,
            (mall, category, product_id, cutoff),
        ).fetchone()
    return row is not None


def record_posting(mall: str, category: str, product_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO postings (mall, category, product_id, posted_at) VALUES (?, ?, ?, ?)",
            (mall, category, product_id, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
