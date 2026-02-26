import logging
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src import db
from src.x_api import get_user_id, get_user_tweets
from src.config import WATCHED_ACCOUNTS, POLL_INTERVAL_MINUTES

logger = logging.getLogger(__name__)


async def fetch_account(handle: str) -> None:
    """Fetch new tweets for a single account and persist them."""
    try:
        row = next((a for a in db.get_watched_accounts() if a["handle"] == handle), None)
        user_id = row["user_id"] if row and row["user_id"] else None

        if not user_id:
            user_id = await get_user_id(handle)
            db.upsert_watched_account(handle, user_id)

        since_id = db.get_latest_tweet_id(handle)
        tweets = await get_user_tweets(user_id, handle, since_id=since_id)
        new_count = db.insert_tweets(tweets)
        db.update_last_fetched(handle)
        logger.info("@%s: %d new tweets saved (total fetched: %d)", handle, new_count, len(tweets))
    except Exception as e:
        logger.error("Error fetching @%s: %s", handle, e, exc_info=True)


async def fetch_all_accounts() -> None:
    logger.info("=== Poll cycle start ===")
    for handle in WATCHED_ACCOUNTS:
        await fetch_account(handle)
    logger.info("=== Poll cycle done ===")


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        fetch_all_accounts,
        trigger=IntervalTrigger(minutes=POLL_INTERVAL_MINUTES),
        id="fetch_all",
        replace_existing=True,
    )
    return scheduler
