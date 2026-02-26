"""
Session health tracking and Telegram alerting.

Tracks consecutive failed poll cycles. On first failure, the scheduler
triggers a proactive session refresh. At HEALTH_ALERT_THRESHOLD consecutive
failures, a Telegram message is sent.
"""

import logging

import httpx

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, HEALTH_ALERT_THRESHOLD

logger = logging.getLogger(__name__)


class FailureTracker:
    def __init__(self) -> None:
        self._consecutive: int = 0

    def record_failure(self) -> int:
        """Increment counter, return new count."""
        self._consecutive += 1
        return self._consecutive

    def record_success(self) -> None:
        if self._consecutive > 0:
            logger.info("Poll cycle succeeded — resetting failure counter (was %d).", self._consecutive)
        self._consecutive = 0

    def reset(self) -> None:
        self._consecutive = 0

    @property
    def count(self) -> int:
        return self._consecutive

    def should_alert(self) -> bool:
        return self._consecutive >= HEALTH_ALERT_THRESHOLD


async def send_telegram_alert(message: str) -> None:
    """Send a message via Telegram Bot API. Silently logs errors."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured — skipping alert. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            logger.info("Telegram alert sent.")
        else:
            logger.error("Telegram alert failed: %d %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.error("Telegram alert error: %s", e)
