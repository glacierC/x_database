import os
from dotenv import load_dotenv

load_dotenv()

WATCHED_ACCOUNTS: list[str] = [
    a.strip() for a in os.getenv("WATCHED_ACCOUNTS", "").split(",") if a.strip()
]
POLL_INTERVAL_MINUTES: int = int(os.getenv("POLL_INTERVAL_MINUTES", "30"))
COOKIES_PATH: str = os.getenv("COOKIES_PATH", "./cookies/cookies.json")
DB_PATH: str = os.getenv("DB_PATH", "./data/tweets.db")

# X web app static bearer token (public, embedded in x.com JS bundle)
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
