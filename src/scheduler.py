import logging
import asyncio
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src import db
from src.x_api import get_user_id, get_user_tweets, get_list_members
from src.auth import refresh_session
from src.config import WATCHED_ACCOUNTS, POLL_INTERVAL_MINUTES, RAW_JSON_RETENTION_DAYS, X_LIST_ID, FETCH_DELAY_SECONDS
from src.health import FailureTracker, send_telegram_alert
from src.exporter import export_all_groups

logger = logging.getLogger(__name__)

_tracker = FailureTracker()


async def fetch_account(handle: str) -> bool:
    """Fetch new tweets for a single account. Returns True on success."""
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
        return True
    except Exception as e:
        logger.error("Error fetching @%s: %s", handle, e, exc_info=True)
        return False


async def fetch_all_accounts() -> None:
    t0 = time.monotonic()
    accounts = db.get_watched_accounts()
    handles = [a["handle"] for a in accounts] if accounts else WATCHED_ACCOUNTS

    total_new = 0
    failed: list[str] = []
    for i, handle in enumerate(handles):
        ok = await fetch_account(handle)
        if not ok:
            failed.append(handle)
        if i < len(handles) - 1:
            await asyncio.sleep(FETCH_DELAY_SECONDS)

    # 汇总新增推文数（从各账号日志里取不到了，改为在 fetch_account 返回值里传）
    elapsed = time.monotonic() - t0
    logger.info(
        "[CYCLE] accounts=%d  failed=%d  duration=%.0fs",
        len(handles), len(failed), elapsed,
    )

    if failed:
        fail_count = _tracker.record_failure()
        logger.warning("Poll cycle: %d/%d accounts failed (consecutive cycles: %d). Failed: %s",
                       len(failed), len(handles), fail_count, failed)

        # First failure → proactive session refresh
        if fail_count == 1:
            logger.info("Triggering proactive session refresh...")
            try:
                await refresh_session()
                logger.info("Proactive refresh done.")
            except Exception as e:
                logger.error("Proactive refresh failed: %s", e)

        # Alert threshold reached → send Telegram
        if _tracker.should_alert():
            msg = (
                f"🚨 <b>x_database alert</b>\n"
                f"連続 {fail_count} cycle 抓取失敗\n"
                f"最新失敗帳號: {', '.join(f'@{h}' for h in failed)}\n"
                f"請檢查 session / cookies 狀態。"
            )
            await send_telegram_alert(msg)
            _tracker.reset()
    else:
        _tracker.record_success()


async def sync_watched_list() -> None:
    """Sync watched_accounts from the configured X List (X_LIST_ID).

    Skipped silently if X_LIST_ID is not set.
    """
    if not X_LIST_ID:
        return
    logger.info("List sync: fetching members for list_id=%s", X_LIST_ID)
    try:
        handles = await get_list_members(X_LIST_ID)
        added, removed = db.sync_from_list(handles)
        logger.info("List sync done: +%d added, -%d removed", added, removed)
    except Exception as e:
        logger.error("List sync failed: %s", e, exc_info=True)


async def run_maintenance() -> None:
    """Daily job: degrade raw_json for tweets older than RAW_JSON_RETENTION_DAYS."""
    if RAW_JSON_RETENTION_DAYS <= 0:
        return
    count = db.degrade_old_raw_json(RAW_JSON_RETENTION_DAYS)
    if count:
        logger.info("Maintenance: cleared raw_json for %d tweets older than %d days.",
                    count, RAW_JSON_RETENTION_DAYS)


async def run_daily_export() -> None:
    """Daily job: export all groups to JSON for downstream consumption."""
    try:
        result = export_all_groups(since_hours=24)
        logger.info("Daily export done: %d groups exported. %s", len(result), result)
    except Exception as e:
        logger.error("Daily export failed: %s", e, exc_info=True)


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        fetch_all_accounts,
        trigger=IntervalTrigger(minutes=POLL_INTERVAL_MINUTES),
        id="fetch_all",
        replace_existing=True,
        max_instances=1,   # 同一时间只允许 1 个实例跑，防止 cycle 重叠
        coalesce=True,     # 积压触发时只跑一次，不补跑
    )
    scheduler.add_job(
        run_maintenance,
        trigger="cron",
        hour=3,
        minute=0,
        id="daily_maintenance",
        replace_existing=True,
    )
    scheduler.add_job(
        run_daily_export,
        trigger="cron",
        hour=6,
        minute=0,
        id="daily_export",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    if X_LIST_ID:
        scheduler.add_job(
            sync_watched_list,
            trigger="cron",
            hour=0,
            minute=5,
            id="daily_list_sync",
            replace_existing=True,
        )
    return scheduler
