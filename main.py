import asyncio
import logging
import os
from pathlib import Path

from src.config import DB_PATH, WATCHED_ACCOUNTS, POLL_INTERVAL_MINUTES
from src.db import init_db, upsert_watched_account
from src.scheduler import build_scheduler, fetch_all_accounts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # Ensure data directory exists
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting x_scraper")
    logger.info("Watched accounts: %s", WATCHED_ACCOUNTS)
    logger.info("Poll interval: %d minutes", POLL_INTERVAL_MINUTES)
    logger.info("DB path: %s", DB_PATH)

    init_db()

    # Seed watched_accounts table from config
    for handle in WATCHED_ACCOUNTS:
        upsert_watched_account(handle)

    # Run immediately on startup, then on schedule
    await fetch_all_accounts()

    scheduler = build_scheduler()
    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to stop.")

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
