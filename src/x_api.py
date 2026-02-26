import json
import logging
from typing import Any

import httpx

from src.auth import get_tokens, refresh_session
from src.config import BEARER_TOKEN

logger = logging.getLogger(__name__)

# X internal GraphQL query IDs (periodically change; update as needed)
QUERY_ID_USER_BY_SCREEN_NAME = "NimuplG1OB7Fd2btCLdBOw"
QUERY_ID_USER_TWEETS = "V7H0Ap3_Hh2FyS75OCDO3Q"

FEATURES_USER_BY_SCREEN_NAME = json.dumps({
    "hidden_profile_subscriptions_enabled": True,
    "rweb_tipjar_consumption_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "subscriptions_verification_info_is_identity_verified_enabled": True,
    "subscriptions_verification_info_verified_since_enabled": True,
    "highlights_tweets_tab_ui_enabled": True,
    "responsive_web_twitter_article_notes_tab_enabled": True,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
})

FEATURES_USER_TWEETS = json.dumps({
    "rweb_tipjar_consumption_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "articles_preview_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "rweb_video_timestamps_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
})


def _build_client(auth_token: str, ct0: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "x-csrf-token": ct0,
            "Cookie": f"auth_token={auth_token}; ct0={ct0}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


async def _api_get(url: str, params: dict, retry: bool = True) -> dict:
    auth_token, ct0 = await get_tokens()
    async with _build_client(auth_token, ct0) as client:
        resp = await client.get(url, params=params)

    if resp.status_code == 401 and retry:
        logger.warning("401 received, refreshing session and retrying...")
        await refresh_session()
        return await _api_get(url, params, retry=False)

    if resp.status_code != 200:
        raise RuntimeError(f"X API error {resp.status_code}: {resp.text[:300]}")

    return resp.json()


async def get_user_id(handle: str) -> str:
    """Resolve a Twitter handle to a numeric user ID."""
    url = f"https://x.com/i/api/graphql/{QUERY_ID_USER_BY_SCREEN_NAME}/UserByScreenName"
    variables = json.dumps({"screen_name": handle, "withSafetyModeUserFields": True})
    params = {
        "variables": variables,
        "features": FEATURES_USER_BY_SCREEN_NAME,
        "fieldToggles": json.dumps({"withAuxiliaryUserLabels": False}),
    }
    data = await _api_get(url, params)
    try:
        user_id = data["data"]["user"]["result"]["rest_id"]
        logger.info("Resolved @%s → user_id=%s", handle, user_id)
        return user_id
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"Could not resolve user_id for @{handle}: {e}\nResponse: {data}")


def _parse_tweet(result: dict, author_handle: str) -> dict | None:
    """Extract a flat tweet dict from a GraphQL result node."""
    try:
        legacy = result.get("legacy") or result.get("tweet", {}).get("legacy", {})
        if not legacy:
            return None

        tweet_id = result.get("rest_id") or result.get("tweet", {}).get("rest_id", "")
        author_id = legacy.get("user_id_str", "")
        full_text = legacy.get("full_text", "")
        created_at = legacy.get("created_at", "")
        rt_count = legacy.get("retweet_count", 0)
        like_count = legacy.get("favorite_count", 0)
        reply_count = legacy.get("reply_count", 0)
        is_retweet = 1 if full_text.startswith("RT @") else 0

        return {
            "id": tweet_id,
            "author_id": author_id,
            "author_handle": author_handle,
            "full_text": full_text,
            "created_at": created_at,
            "retweet_count": rt_count,
            "like_count": like_count,
            "reply_count": reply_count,
            "is_retweet": is_retweet,
            "raw_json": json.dumps(result),
        }
    except Exception as e:
        logger.debug("Failed to parse tweet node: %s", e)
        return None


async def get_user_tweets(
    user_id: str,
    handle: str,
    since_id: str | None = None,
    max_pages: int = 10,
) -> list[dict]:
    """
    Fetch tweets for user_id. Stops when since_id is encountered or max_pages reached.
    Returns list of parsed tweet dicts (newest first).
    """
    url = f"https://x.com/i/api/graphql/{QUERY_ID_USER_TWEETS}/UserTweets"
    tweets: list[dict] = []
    cursor: str | None = None

    for page in range(max_pages):
        variables: dict[str, Any] = {
            "userId": user_id,
            "count": 40,
            "includePromotedContent": False,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
        }
        if cursor:
            variables["cursor"] = cursor

        params = {
            "variables": json.dumps(variables),
            "features": FEATURES_USER_TWEETS,
            "fieldToggles": json.dumps({"withArticlePlainText": False}),
        }

        data = await _api_get(url, params)

        # Navigate to timeline instructions
        try:
            instructions = (
                data["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"]
            )
        except (KeyError, TypeError):
            logger.warning("Unexpected response shape for user_id=%s page=%d", user_id, page)
            break

        next_cursor: str | None = None
        stop_fetching = False

        for instruction in instructions:
            if instruction.get("type") != "TimelineAddEntries":
                continue
            for entry in instruction.get("entries", []):
                entry_id: str = entry.get("entryId", "")

                # Cursor entry
                if "cursor-bottom" in entry_id:
                    content = entry.get("content", {})
                    next_cursor = content.get("value")
                    continue

                # Tweet entry
                content = entry.get("content", {})
                item_content = content.get("itemContent", {})
                tweet_results = item_content.get("tweet_results", {})
                result = tweet_results.get("result", {})

                # Handle tombstone / unavailable tweets
                if result.get("__typename") in ("TweetTombstone", "TweetUnavailable"):
                    continue

                parsed = _parse_tweet(result, handle)
                if parsed is None:
                    continue

                if since_id and parsed["id"] == since_id:
                    stop_fetching = True
                    break

                tweets.append(parsed)

            if stop_fetching:
                break

        if stop_fetching or not next_cursor:
            break

        cursor = next_cursor
        logger.debug("Fetched page %d for @%s, cursor=%s…", page + 1, handle, cursor[:20])

    logger.info("Fetched %d tweets for @%s", len(tweets), handle)
    return tweets
