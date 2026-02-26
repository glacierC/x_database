import sqlite3
import logging
from datetime import datetime, timezone
from src.config import DB_PATH

logger = logging.getLogger(__name__)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Idempotent schema setup."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tweets (
                id TEXT PRIMARY KEY,
                author_id TEXT NOT NULL,
                author_handle TEXT NOT NULL,
                full_text TEXT,
                created_at TEXT,
                retweet_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                is_retweet INTEGER DEFAULT 0,
                raw_json TEXT,
                fetched_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS watched_accounts (
                handle TEXT PRIMARY KEY,
                user_id TEXT,
                last_fetched_at TEXT
            );
        """)
    logger.info("DB initialized at %s", DB_PATH)


def upsert_watched_account(handle: str, user_id: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO watched_accounts (handle, user_id)
            VALUES (?, ?)
            ON CONFLICT(handle) DO UPDATE SET
                user_id = COALESCE(excluded.user_id, watched_accounts.user_id)
            """,
            (handle, user_id),
        )


def get_watched_accounts() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM watched_accounts").fetchall()
    return [dict(r) for r in rows]


def get_latest_tweet_id(handle: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM tweets WHERE author_handle = ? ORDER BY id DESC LIMIT 1",
            (handle,),
        ).fetchone()
    return row["id"] if row else None


def insert_tweets(tweets: list[dict]) -> int:
    """Insert tweets, skip duplicates. Returns count of newly inserted rows."""
    if not tweets:
        return 0
    inserted = 0
    with get_conn() as conn:
        for t in tweets:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO tweets
                    (id, author_id, author_handle, full_text, created_at,
                     retweet_count, like_count, reply_count, is_retweet, raw_json, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    t["id"],
                    t["author_id"],
                    t["author_handle"],
                    t["full_text"],
                    t["created_at"],
                    t.get("retweet_count", 0),
                    t.get("like_count", 0),
                    t.get("reply_count", 0),
                    t.get("is_retweet", 0),
                    t["raw_json"],
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            inserted += cur.rowcount
    return inserted


def update_last_fetched(handle: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE watched_accounts SET last_fetched_at = ? WHERE handle = ?",
            (datetime.now(timezone.utc).isoformat(), handle),
        )
