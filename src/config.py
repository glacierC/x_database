import os
from dotenv import load_dotenv

load_dotenv()

WATCHED_ACCOUNTS: list[str] = [
    a.strip() for a in os.getenv("WATCHED_ACCOUNTS", "").split(",") if a.strip()
]
POLL_INTERVAL_MINUTES: int = int(os.getenv("POLL_INTERVAL_MINUTES", "30"))
COOKIES_PATH: str = os.getenv("COOKIES_PATH", "./cookies/cookies.json")
DB_PATH: str = os.getenv("DB_PATH", "./data/tweets.db")

# Telegram alerting (optional — leave blank to disable)
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
HEALTH_ALERT_THRESHOLD: int = int(os.getenv("HEALTH_ALERT_THRESHOLD", "3"))

# Data lifecycle: raw_json is set to NULL after this many days (0 = keep forever)
RAW_JSON_RETENTION_DAYS: int = int(os.getenv("RAW_JSON_RETENTION_DAYS", "90"))

# X List sync (optional — leave blank to disable)
# Set to the numeric ID from the List URL: x.com/i/lists/<X_LIST_ID>
X_LIST_ID: str = os.getenv("X_LIST_ID", "")

# X web app static bearer token (public, embedded in x.com JS bundle)
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
