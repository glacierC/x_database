import json
import logging
import os
from pathlib import Path
from playwright.async_api import async_playwright

from src.config import COOKIES_PATH

logger = logging.getLogger(__name__)

_cached_tokens: dict[str, str] = {}


def load_cookies() -> list[dict]:
    path = Path(COOKIES_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"cookies.json not found at {COOKIES_PATH}. "
            "Please export your X session cookies first (see README)."
        )
    with open(path) as f:
        return json.load(f)


def _save_cookies(cookies: list[dict]) -> None:
    path = Path(COOKIES_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(cookies, f, indent=2)
    logger.info("Cookies saved to %s", COOKIES_PATH)


def _extract_tokens(cookies: list[dict]) -> tuple[str, str]:
    auth_token = next((c["value"] for c in cookies if c["name"] == "auth_token"), "")
    ct0 = next((c["value"] for c in cookies if c["name"] == "ct0"), "")
    return auth_token, ct0


async def refresh_session() -> tuple[str, str]:
    """
    Launch headless Chromium, load saved cookies, visit x.com to refresh session,
    then save updated cookies and return (auth_token, ct0).
    """
    logger.info("Refreshing X session via Playwright...")
    cookies = load_cookies()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(cookies)

        page = await context.new_page()
        try:
            await page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            logger.warning("Page load warning (non-fatal): %s", e)

        updated_cookies = await context.cookies()
        await browser.close()

    _save_cookies(updated_cookies)

    auth_token, ct0 = _extract_tokens(updated_cookies)
    if not auth_token or not ct0:
        raise RuntimeError(
            "Session appears invalid: auth_token or ct0 missing after refresh. "
            "Please re-export cookies from a logged-in browser session."
        )

    _cached_tokens["auth_token"] = auth_token
    _cached_tokens["ct0"] = ct0
    logger.info("Session refreshed successfully.")
    return auth_token, ct0


async def get_tokens() -> tuple[str, str]:
    """Return cached tokens, refreshing if not yet loaded."""
    if _cached_tokens.get("auth_token") and _cached_tokens.get("ct0"):
        return _cached_tokens["auth_token"], _cached_tokens["ct0"]

    # Try loading from file first (no Playwright needed)
    try:
        cookies = load_cookies()
        auth_token, ct0 = _extract_tokens(cookies)
        if auth_token and ct0:
            _cached_tokens["auth_token"] = auth_token
            _cached_tokens["ct0"] = ct0
            logger.info("Tokens loaded from cookies.json (no refresh needed).")
            return auth_token, ct0
    except FileNotFoundError:
        raise

    # Tokens missing from file → full refresh
    return await refresh_session()
