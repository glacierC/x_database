import asyncio
import json
import logging
import time
from typing import Any

import httpx

from src.auth import get_tokens, refresh_session
from src.config import BEARER_TOKEN, INITIAL_MAX_PAGES

logger = logging.getLogger(__name__)

# X internal GraphQL query IDs (periodically change; update as needed)
QUERY_ID_USER_BY_SCREEN_NAME = "NimuplG1OB7Fd2btCLdBOw"
QUERY_ID_USER_TWEETS = "V7H0Ap3_Hh2FyS75OCDO3Q"
# ListMembers query ID — obtain by opening an X List page and checking Network tab for ListMembers
QUERY_ID_LIST_MEMBERS = "NUsHx0_C0Vva49NlIorkcQ"

FEATURES_LIST_MEMBERS = json.dumps({
    "rweb_video_screen_enabled": False,
    "profile_label_improvements_pcf_label_in_post_enabled": True,
    "responsive_web_profile_redirect_enabled": False,
    "rweb_tipjar_consumption_enabled": False,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "premium_content_api_read_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
    "responsive_web_grok_analyze_post_followups_enabled": True,
    "responsive_web_jetfuel_frame": True,
    "responsive_web_grok_share_attachment_enabled": True,
    "responsive_web_grok_annotations_enabled": True,
    "articles_preview_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "responsive_web_grok_show_grok_translated_post": False,
    "responsive_web_grok_analysis_button_from_backend": True,
    "post_ctas_fetch_enabled": True,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_grok_image_annotation_enabled": True,
    "responsive_web_grok_imagine_annotation_enabled": True,
    "responsive_web_grok_community_note_auto_translation_is_enabled": False,
    "responsive_web_enhance_cards_enabled": False,
})

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

    if resp.status_code == 429 and retry:
        reset_ts = resp.headers.get("x-rate-limit-reset")
        if reset_ts:
            wait = max(10, int(reset_ts) - int(time.time()) + 10)
        else:
            wait = 60
        logger.warning("429 rate limited. Sleeping %ds before retry...", wait)
        await asyncio.sleep(wait)
        return await _api_get(url, params, retry=False)

    if resp.status_code != 200:
        raise RuntimeError(f"X API error {resp.status_code}: {resp.text[:300]}")

    return resp.json()


async def get_list_members(list_id: str) -> list[str]:
    """Fetch all member handles from an X List. Returns lowercase handles.

    Requires QUERY_ID_LIST_MEMBERS to be set (sniff from x.com network traffic).
    """
    if not QUERY_ID_LIST_MEMBERS:
        raise RuntimeError(
            "QUERY_ID_LIST_MEMBERS is not set. "
            "Open an X List page in browser → F12 → Network → filter 'ListMembers' "
            "→ copy the query ID from the URL."
        )

    url = f"https://x.com/i/api/graphql/{QUERY_ID_LIST_MEMBERS}/ListMembers"
    handles: list[str] = []
    cursor: str | None = None

    for page in range(20):  # safety limit: 20 pages × 100 = 2000 members
        variables: dict = {
            "listId": list_id,
            "count": 100,
            "withSafetyModeUserFields": True,
        }
        if cursor:
            variables["cursor"] = cursor

        params = {
            "variables": json.dumps(variables),
            "features": FEATURES_LIST_MEMBERS,
        }

        data = await _api_get(url, params)

        try:
            instructions = (
                data["data"]["list"]["members_timeline"]["timeline"]["instructions"]
            )
        except (KeyError, TypeError):
            logger.warning("Unexpected ListMembers response shape (page %d): %s", page, str(data)[:200])
            break

        next_cursor: str | None = None
        found_entries = False

        for instruction in instructions:
            if instruction.get("type") == "TimelineAddEntries":
                for entry in instruction.get("entries", []):
                    entry_id: str = entry.get("entryId", "")
                    if "cursor-bottom" in entry_id:
                        next_cursor = entry.get("content", {}).get("value")
                        continue
                    # User entry — screen_name in core.screen_name (new API) or legacy.screen_name
                    content = entry.get("content", {})
                    item_content = content.get("itemContent", {})
                    user_results = item_content.get("user_results", {})
                    result = user_results.get("result", {})
                    screen_name = (
                        result.get("core", {}).get("screen_name")
                        or result.get("legacy", {}).get("screen_name", "")
                    )
                    if screen_name:
                        handles.append(screen_name.lower())
                        found_entries = True

        if not found_entries or not next_cursor:
            break
        cursor = next_cursor
        logger.debug("ListMembers page %d: %d total so far", page + 1, len(handles))

    logger.info("X List %s: fetched %d member handles", list_id, len(handles))
    return handles


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

        # Quote tweet (S0004)
        quoted = result.get("quoted_status_result", {}).get("result", {})
        quoted_tweet_id = quoted.get("rest_id") if quoted else None
        quoted_full_text = quoted.get("legacy", {}).get("full_text") if quoted else None
        quoted_author_handle = (
            quoted.get("core", {}).get("user_results", {})
            .get("result", {}).get("legacy", {}).get("screen_name")
        ) if quoted else None

        # Media attachments (S0005)
        ext = legacy.get("extended_entities") or legacy.get("entities") or {}
        media_items = []
        for m in ext.get("media", []):
            video_url = None
            if m.get("type") in ("video", "animated_gif"):
                variants = m.get("video_info", {}).get("variants", [])
                mp4s = [v for v in variants if v.get("content_type") == "video/mp4"]
                if mp4s:
                    video_url = max(mp4s, key=lambda v: v.get("bitrate", 0)).get("url")
            media_items.append({
                "id": m.get("id_str", ""),
                "tweet_id": tweet_id,
                "media_type": m.get("type"),
                "url": m.get("media_url_https"),
                "video_url": video_url,
            })

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
            "quoted_tweet_id": quoted_tweet_id,
            "quoted_full_text": quoted_full_text,
            "quoted_author_handle": quoted_author_handle,
            "media_items": media_items,
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
    # Cap pages on initial fetch (no since_id) to avoid exhausting rate limit budget
    effective_max_pages = max_pages if since_id else min(max_pages, INITIAL_MAX_PAGES)

    for page in range(effective_max_pages):
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
        logger.debug("Fetched page %d/%d for @%s, cursor=%s…", page + 1, effective_max_pages, handle, cursor[:20])

    logger.info("Fetched %d tweets for @%s", len(tweets), handle)
    return tweets
