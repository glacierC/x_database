"""Daily export utilities (S0008).

Exports tweet data per group to JSON files for downstream consumption.
"""
import json
import logging
import os
import sqlite3
from datetime import date

from src.config import DB_PATH
from src.db import get_conn, get_groups, _ensure_group_tables

logger = logging.getLogger(__name__)


def export_group_to_json(
    group_name: str,
    since_hours: int = 24,
    original_only: bool = True,
) -> list[dict]:
    """Return all tweets for a group as a list of dicts with media_urls aggregated."""
    original_filter = "AND t.is_retweet = 0" if original_only else ""
    sql = f"""
        SELECT t.id, t.author_handle, t.full_text, t.created_at,
               t.like_count, t.retweet_count, t.reply_count, t.is_retweet,
               t.quoted_tweet_id, t.quoted_author_handle, t.quoted_full_text,
               GROUP_CONCAT(m.url) AS media_urls
        FROM tweets t
        JOIN account_group_members gm ON t.author_handle = gm.handle
        LEFT JOIN media m ON m.tweet_id = t.id
        WHERE gm.group_name = ?
          AND t.fetched_at >= datetime('now', ? || ' hours')
          {original_filter}
        GROUP BY t.id
        ORDER BY t.id DESC
    """
    with get_conn() as conn:
        _ensure_group_tables(conn)
        rows = conn.execute(sql, (group_name, f"-{since_hours}")).fetchall()

    result = []
    for row in rows:
        d = dict(row)
        raw = d.get("media_urls")
        d["media_urls"] = raw.split(",") if raw else []
        result.append(d)
    return result


def export_all_groups(
    since_hours: int = 24,
    output_dir: str = "data/exports",
) -> dict[str, str]:
    """Export all groups to {output_dir}/YYYY-MM-DD/<group>.json.

    Returns {group_name: file_path}.
    """
    today = date.today().isoformat()
    day_dir = os.path.join(output_dir, today)
    os.makedirs(day_dir, exist_ok=True)

    groups = get_groups()
    result: dict[str, str] = {}

    for group in groups:
        name = group["name"]
        try:
            tweets = export_group_to_json(name, since_hours=since_hours)
            file_path = os.path.join(day_dir, f"{name}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(tweets, f, ensure_ascii=False, indent=2)
            result[name] = file_path
            logger.info("Exported %d tweets for group '%s' → %s", len(tweets), name, file_path)
        except Exception as e:
            logger.error("Failed to export group '%s': %s", name, e, exc_info=True)

    return result
