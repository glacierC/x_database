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
                quoted_tweet_id TEXT,
                quoted_full_text TEXT,
                quoted_author_handle TEXT,
                raw_json TEXT,
                fetched_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS watched_accounts (
                handle TEXT PRIMARY KEY,
                user_id TEXT,
                last_fetched_at TEXT,
                source TEXT DEFAULT 'manual'
            );

            CREATE TABLE IF NOT EXISTS account_groups (
                name        TEXT PRIMARY KEY,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS account_group_members (
                group_name  TEXT NOT NULL REFERENCES account_groups(name) ON DELETE CASCADE,
                handle      TEXT NOT NULL REFERENCES watched_accounts(handle) ON DELETE CASCADE,
                PRIMARY KEY (group_name, handle)
            );

            CREATE TABLE IF NOT EXISTS media (
                id          TEXT PRIMARY KEY,
                tweet_id    TEXT NOT NULL,
                media_type  TEXT,
                url         TEXT,
                video_url   TEXT
            );

            CREATE TABLE IF NOT EXISTS article_content (
                tweet_id     TEXT PRIMARY KEY,
                title        TEXT,
                content      TEXT,
                fetch_status TEXT DEFAULT 'pending',
                fetched_at   TEXT,
                error_msg    TEXT
            );
        """)
    # Migration: add source column if missing (for existing DBs)
    try:
        conn.execute("ALTER TABLE watched_accounts ADD COLUMN source TEXT DEFAULT 'manual'")
        logger.info("Migration: added 'source' column to watched_accounts")
    except Exception:
        pass  # Column already exists
    # Migration: add is_article column (S0013)
    try:
        conn.execute("ALTER TABLE tweets ADD COLUMN is_article INTEGER DEFAULT 0")
        logger.info("Migration: added 'is_article' column to tweets")
    except Exception:
        pass

    # Migration: add quote tweet columns (S0004)
    for col_sql, col_name in [
        ("ALTER TABLE tweets ADD COLUMN quoted_tweet_id TEXT", "quoted_tweet_id"),
        ("ALTER TABLE tweets ADD COLUMN quoted_full_text TEXT", "quoted_full_text"),
        ("ALTER TABLE tweets ADD COLUMN quoted_author_handle TEXT", "quoted_author_handle"),
    ]:
        try:
            conn.execute(col_sql)
            logger.info("Migration: added '%s' column to tweets", col_name)
        except Exception:
            pass  # Column already exists

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


def insert_media(media_items: list[dict]) -> None:
    """Batch-insert media records, skip duplicates."""
    if not media_items:
        return
    with get_conn() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO media (id, tweet_id, media_type, url, video_url)
            VALUES (:id, :tweet_id, :media_type, :url, :video_url)
            """,
            media_items,
        )


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
                     retweet_count, like_count, reply_count, is_retweet, is_article,
                     quoted_tweet_id, quoted_full_text, quoted_author_handle,
                     raw_json, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    t.get("is_article", 0),
                    t.get("quoted_tweet_id"),
                    t.get("quoted_full_text"),
                    t.get("quoted_author_handle"),
                    t["raw_json"],
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            inserted += cur.rowcount
            if cur.rowcount and t.get("media_items"):
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO media (id, tweet_id, media_type, url, video_url)
                    VALUES (:id, :tweet_id, :media_type, :url, :video_url)
                    """,
                    t["media_items"],
                )
    return inserted


def update_last_fetched(handle: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE watched_accounts SET last_fetched_at = ? WHERE handle = ?",
            (datetime.now(timezone.utc).isoformat(), handle),
        )


# ── Group tables (added in v0.2) ─────────────────────────────────────────────

def _ensure_group_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS account_groups (
            name        TEXT PRIMARY KEY,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS account_group_members (
            group_name  TEXT NOT NULL REFERENCES account_groups(name) ON DELETE CASCADE,
            handle      TEXT NOT NULL REFERENCES watched_accounts(handle) ON DELETE CASCADE,
            PRIMARY KEY (group_name, handle)
        );
    """)


def add_watched_account(handle: str, source: str = "manual") -> None:
    """Add an account to watched_accounts (no-op if already exists)."""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watched_accounts (handle, source) VALUES (?, ?)",
            (handle, source),
        )


def remove_watched_account(handle: str) -> None:
    """Remove account and all its group memberships."""
    with get_conn() as conn:
        _ensure_group_tables(conn)
        conn.execute("DELETE FROM account_group_members WHERE handle = ?", (handle,))
        conn.execute("DELETE FROM watched_accounts WHERE handle = ?", (handle,))


def create_group(name: str, description: str = "") -> None:
    """Create a group (no-op if already exists)."""
    with get_conn() as conn:
        _ensure_group_tables(conn)
        conn.execute(
            "INSERT OR IGNORE INTO account_groups (name, description) VALUES (?, ?)",
            (name, description),
        )


def assign_to_group(group_name: str, handle: str) -> None:
    """Add an account to a group. Both must already exist."""
    with get_conn() as conn:
        _ensure_group_tables(conn)
        conn.execute(
            "INSERT OR IGNORE INTO account_group_members (group_name, handle) VALUES (?, ?)",
            (group_name, handle),
        )


def unassign_from_group(group_name: str, handle: str) -> None:
    with get_conn() as conn:
        _ensure_group_tables(conn)
        conn.execute(
            "DELETE FROM account_group_members WHERE group_name = ? AND handle = ?",
            (group_name, handle),
        )


def get_groups() -> list[dict]:
    with get_conn() as conn:
        _ensure_group_tables(conn)
        rows = conn.execute("SELECT * FROM account_groups ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def get_group_members(group_name: str) -> list[str]:
    with get_conn() as conn:
        _ensure_group_tables(conn)
        rows = conn.execute(
            "SELECT handle FROM account_group_members WHERE group_name = ? ORDER BY handle",
            (group_name,),
        ).fetchall()
    return [r["handle"] for r in rows]


def sync_from_list(handles: list[str]) -> tuple[int, int]:
    """Sync watched_accounts from an X List.

    - INSERT new handles with source='list_sync'
    - DELETE source='list_sync' accounts no longer in the list (tweets are kept)
    Returns (added, removed) counts.
    """
    with get_conn() as conn:
        existing_list_sync = {
            r[0] for r in conn.execute(
                "SELECT handle FROM watched_accounts WHERE source = 'list_sync'"
            ).fetchall()
        }
        handle_set = {h.lower() for h in handles}

        to_add = handle_set - {h.lower() for h in existing_list_sync}
        to_remove = {h for h in existing_list_sync if h.lower() not in handle_set}

        for h in to_add:
            conn.execute(
                "INSERT OR IGNORE INTO watched_accounts (handle, source) VALUES (?, 'list_sync')",
                (h,),
            )

        for h in to_remove:
            conn.execute("DELETE FROM account_group_members WHERE handle = ?", (h,))
            conn.execute(
                "DELETE FROM watched_accounts WHERE handle = ? AND source = 'list_sync'",
                (h,),
            )

    logger.info("List sync: +%d added, -%d removed", len(to_add), len(to_remove))
    return len(to_add), len(to_remove)


def degrade_old_raw_json(days: int = 90) -> int:
    """Set raw_json = NULL for tweets fetched more than `days` days ago. Returns count updated.

    Uses fetched_at (ISO 8601) not created_at (Twitter's non-ISO format).
    """
    if days <= 0:
        return 0
    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE tweets
               SET raw_json = NULL
             WHERE raw_json IS NOT NULL
               AND fetched_at < datetime('now', ? || ' days')
            """,
            (f"-{days}",),
        )
    return cur.rowcount


def get_tweets_by_group(
    group_name: str,
    since_hours: int = 24,
    original_only: bool = True,
) -> list[dict]:
    """Return tweets from all accounts in a group, newest first."""
    query = """
        SELECT t.*
        FROM tweets t
        JOIN account_group_members m ON t.author_handle = m.handle
        WHERE m.group_name = ?
          AND t.created_at >= datetime('now', ? || ' hours')
          {}
        ORDER BY t.id DESC
    """.format("AND t.is_retweet = 0" if original_only else "")
    with get_conn() as conn:
        _ensure_group_tables(conn)
        rows = conn.execute(query, (group_name, f"-{since_hours}")).fetchall()
    return [dict(r) for r in rows]


# ── Extended query interfaces (added in S0007) ────────────────────────────────

def get_tweets(
    handle: str,
    since_hours: int = 24,
    original_only: bool = True,
) -> list[dict]:
    """Return tweets for a single account, newest first."""
    original_filter = "AND t.is_retweet = 0" if original_only else ""
    query = f"""
        SELECT t.*
        FROM tweets t
        WHERE t.author_handle = ?
          AND t.fetched_at >= datetime('now', ? || ' hours')
          {original_filter}
        ORDER BY t.id DESC
    """
    with get_conn() as conn:
        rows = conn.execute(query, (handle, f"-{since_hours}")).fetchall()
    return [dict(r) for r in rows]


def search_tweets(
    query: str,
    group_name: str | None = None,
    since_hours: int = 24,
    original_only: bool = True,
) -> list[dict]:
    """Full-text keyword search. Optionally scoped to a group."""
    like = f"%{query}%"
    original_filter = "AND t.is_retweet = 0" if original_only else ""
    if group_name is not None:
        sql = f"""
            SELECT t.*
            FROM tweets t
            JOIN account_group_members gm ON t.author_handle = gm.handle
            WHERE gm.group_name = ?
              AND (t.full_text LIKE ? OR t.quoted_full_text LIKE ?)
              AND t.fetched_at >= datetime('now', ? || ' hours')
              {original_filter}
            ORDER BY t.id DESC
        """
        params = (group_name, like, like, f"-{since_hours}")
    else:
        sql = f"""
            SELECT t.*
            FROM tweets t
            WHERE (t.full_text LIKE ? OR t.quoted_full_text LIKE ?)
              AND t.fetched_at >= datetime('now', ? || ' hours')
              {original_filter}
            ORDER BY t.id DESC
        """
        params = (like, like, f"-{since_hours}")
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_tweets_with_media(
    group_name: str,
    since_hours: int = 24,
) -> list[dict]:
    """Return tweets that have at least one media attachment."""
    sql = """
        SELECT DISTINCT t.*
        FROM tweets t
        JOIN account_group_members gm ON t.author_handle = gm.handle
        JOIN media m ON m.tweet_id = t.id
        WHERE gm.group_name = ?
          AND t.fetched_at >= datetime('now', ? || ' hours')
        ORDER BY t.id DESC
    """
    with get_conn() as conn:
        _ensure_group_tables(conn)
        rows = conn.execute(sql, (group_name, f"-{since_hours}")).fetchall()
    return [dict(r) for r in rows]


def get_quote_tweets(
    group_name: str,
    since_hours: int = 24,
) -> list[dict]:
    """Return quote tweets (those that reference another tweet)."""
    sql = """
        SELECT t.*
        FROM tweets t
        JOIN account_group_members gm ON t.author_handle = gm.handle
        WHERE gm.group_name = ?
          AND t.fetched_at >= datetime('now', ? || ' hours')
          AND t.quoted_tweet_id IS NOT NULL
        ORDER BY t.id DESC
    """
    with get_conn() as conn:
        _ensure_group_tables(conn)
        rows = conn.execute(sql, (group_name, f"-{since_hours}")).fetchall()
    return [dict(r) for r in rows]


_VALID_METRICS = {"like_count", "retweet_count", "reply_count"}


def get_pending_articles(limit: int = 20) -> list[dict]:
    """Return article tweets whose content hasn't been fetched yet (or failed < 3 times)."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT t.id AS tweet_id, t.author_handle, t.is_article,
                   ac.fetch_status, ac.error_msg
            FROM tweets t
            LEFT JOIN article_content ac ON ac.tweet_id = t.id
            WHERE t.is_article = 1
              AND (ac.tweet_id IS NULL OR ac.fetch_status = 'pending')
            ORDER BY t.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def upsert_article_content(
    tweet_id: str,
    title: str | None,
    content: str | None,
    fetch_status: str,
    error_msg: str | None = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO article_content (tweet_id, title, content, fetch_status, fetched_at, error_msg)
            VALUES (?, ?, ?, ?, datetime('now'), ?)
            ON CONFLICT(tweet_id) DO UPDATE SET
                title        = excluded.title,
                content      = excluded.content,
                fetch_status = excluded.fetch_status,
                fetched_at   = excluded.fetched_at,
                error_msg    = excluded.error_msg
            """,
            (tweet_id, title, content, fetch_status, error_msg),
        )


def get_top_tweets(
    group_name: str,
    since_hours: int = 24,
    limit: int = 10,
    metric: str = "like_count",
    original_only: bool = True,
) -> list[dict]:
    """Return top N tweets by engagement metric (like_count / retweet_count / reply_count)."""
    if metric not in _VALID_METRICS:
        metric = "like_count"
    original_filter = "AND t.is_retweet = 0" if original_only else ""
    sql = f"""
        SELECT t.*
        FROM tweets t
        JOIN account_group_members gm ON t.author_handle = gm.handle
        WHERE gm.group_name = ?
          AND t.fetched_at >= datetime('now', ? || ' hours')
          {original_filter}
        ORDER BY t.{metric} DESC
        LIMIT ?
    """
    with get_conn() as conn:
        _ensure_group_tables(conn)
        rows = conn.execute(sql, (group_name, f"-{since_hours}", limit)).fetchall()
    return [dict(r) for r in rows]
