"""Fetch full article content for X Article tweets via Jina Reader (S0013)."""
import logging
import json

import httpx

from src import db

logger = logging.getLogger(__name__)

JINA_BASE = "https://r.jina.ai/"
MAX_RETRIES = 3


def _article_url(handle: str, tweet_id: str, raw_json_str: str) -> str | None:
    """Construct X article URL. Returns None if not an article.

    URL pattern: https://x.com/<handle>/article/<tweet_id>
    (tweet_id, not the article's internal rest_id)
    """
    try:
        data = json.loads(raw_json_str) if isinstance(raw_json_str, str) else raw_json_str
        if not data.get("article"):
            return None
        return f"https://x.com/{handle}/article/{tweet_id}"
    except Exception:
        return None


async def fetch_article(tweet_id: str, handle: str, raw_json_str: str) -> None:
    """Fetch article content via Jina and write result to article_content table."""
    article_url = _article_url(handle, tweet_id, raw_json_str)
    if not article_url:
        logger.warning("Could not construct article URL for tweet %s", tweet_id)
        db.upsert_article_content(tweet_id, None, None, "failed", "could not construct URL")
        return

    jina_url = JINA_BASE + article_url
    logger.info("Fetching article %s via Jina", article_url)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(jina_url, headers={"Accept": "text/plain"})
        if resp.status_code == 200:
            content = resp.text
            db.upsert_article_content(tweet_id, None, content, "ok")
            logger.info("Article %s fetched OK (%d chars)", tweet_id, len(content))
        else:
            msg = f"HTTP {resp.status_code}"
            db.upsert_article_content(tweet_id, None, None, "failed", msg)
            logger.warning("Jina returned %s for tweet %s", msg, tweet_id)
    except Exception as e:
        db.upsert_article_content(tweet_id, None, None, "failed", str(e))
        logger.error("Jina fetch error for tweet %s: %s", tweet_id, e)


async def run_pending_articles() -> None:
    """Fetch content for all pending articles. Called by scheduler."""
    pending = db.get_pending_articles(limit=20)
    if not pending:
        logger.debug("No pending articles to fetch")
        return

    logger.info("Processing %d pending articles", len(pending))
    for row in pending:
        tweet_id = row["tweet_id"]
        handle = row["author_handle"]

        # Load raw_json to construct URL
        with db.get_conn() as conn:
            r = conn.execute(
                "SELECT raw_json FROM tweets WHERE id = ?", (tweet_id,)
            ).fetchone()

        if not r or not r["raw_json"]:
            db.upsert_article_content(tweet_id, None, None, "failed", "raw_json unavailable")
            continue

        await fetch_article(tweet_id, handle, r["raw_json"])
