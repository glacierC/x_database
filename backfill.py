"""
One-off backfill: fetch last N days of tweets for a given handle and save to DB.

Usage:
    python backfill.py <handle> [days=100]
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta

from src import db
from src.x_api import get_user_id, get_user_tweets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

TWITTER_DATE_FMT = "%a %b %d %H:%M:%S +0000 %Y"
ISO_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def parse_created_at(ts: str) -> datetime | None:
    for fmt in (ISO_DATE_FMT, TWITTER_DATE_FMT):
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            continue
    return None


async def backfill(handle: str, days: int = 100, max_pages: int = 30) -> None:
    db.init_db()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    logger.info("Backfill @%s — cutoff: %s (%d days ago)", handle, cutoff.date(), days)

    # Resolve user_id (reuse cached value if available)
    rows = db.get_watched_accounts()
    row = next((r for r in rows if r["handle"] == handle), None)
    user_id = row["user_id"] if row and row["user_id"] else None

    if not user_id:
        user_id = await get_user_id(handle)
        db.upsert_watched_account(handle, user_id)
        logger.info("Resolved @%s → user_id=%s", handle, user_id)
    else:
        logger.info("Using cached user_id=%s for @%s", user_id, handle)

    # Fetch with large max_pages; no since_id (we want historical data)
    tweets = await get_user_tweets(user_id, handle, since_id=None, max_pages=max_pages)

    # Filter to cutoff window
    kept = []
    for t in tweets:
        dt = parse_created_at(t.get("created_at", ""))
        if dt and dt >= cutoff:
            kept.append(t)

    logger.info(
        "Fetched %d tweets total, keeping %d within last %d days",
        len(tweets), len(kept), days,
    )

    new_count = db.insert_tweets(kept)
    db.update_last_fetched(handle)
    logger.info("Inserted %d new tweets for @%s (skipped %d duplicates)", new_count, handle, len(kept) - new_count)


if __name__ == "__main__":
    handle = sys.argv[1].lstrip("@") if len(sys.argv) > 1 else "turingou"
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    asyncio.run(backfill(handle, days))
