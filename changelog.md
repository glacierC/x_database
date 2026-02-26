# Changelog
# Last Updated: 2026-02-26

## [0.1.0] - 2026-02-26

### Added
- Playwright headless cookie 管理（load / refresh / token 提取）
- X 内部 GraphQL API 客户端（UserByScreenName + UserTweets，httpx 异步）
- SQLite 存储，幂等建表，tweet id 去重（INSERT OR IGNORE）
- APScheduler 30 分钟定时轮询所有 watched accounts
- `.env` 配置（WATCHED_ACCOUNTS / POLL_INTERVAL_MINUTES / DB_PATH / COOKIES_PATH）
- Dockerfile + docker-compose（带 resource limit，无端口暴露）

### Fixed
- `get_latest_tweet_id` 改为按 tweet ID 排序（原按 `created_at` 文本排序会因星期前缀字典序错误导致漏抓新推文）
