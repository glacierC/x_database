# Changelog
# Last Updated: 2026-03-09

## [1.4.0] - 2026-03-09

### Added (S0016 — Web Dashboard)
- `src/dashboard.py`：Flask read-only dashboard，端口 8080
  - Group 概览表（账号数 / 推文 1h / 推文 24h / 最后活跃）
  - 账号状态表（NEVER 红 / STALE>3h 橙 / OK 绿）
  - 近 24h 每小时推文 inline bar chart
  - `<meta http-equiv="refresh" content="60">` 自动刷新
- `docker-compose.yml`：新增 `dashboard` service（`:ro` 只读挂载 data volume，healthcheck curl）
- `requirements.txt`：新增 `flask`

### Changed (架构决策 — 采集上限确认)
- 无头浏览器采集上限确认：~1300 条推文/小时（串行 6s/账号 + 429 封禁窗口）
- 付费 X API 评估：1000 账号规模需 Enterprise 级（$3,500+/月），不经济
- **crypto group 清除**：363 个账号从 account_group_members + watched_accounts 删除
- **staging group 清除**：325 个账号从 account_group_members + watched_accounts 删除
- 当前监控账号：**212 个**（ai_tech 178 / macro 119 / geopolitics 118 / equities 113 / ai 2）
- staging → eval → promote 自动化（S0014/S0015）代码保留，**流程暂停执行**

## [1.3.0] - 2026-03-08

### Added (S0015 — 规范化导入 SOP)
- `import_from_discovery_batch.py` 增强：
  - `--verbose`：显示 eval_reason + 2 条 sample tweets，辅助导入决策
  - `--only-new`：交叉查询 watched_accounts，过滤已有账号
  - `--output-format shell`：输出 `cli.py` 命令序列，用于 VPS 远程导入

### Added (S0014 — Staging 隔离)
- `import_from_discovery_batch.py`：新建，从 x_discovery YES 账号批量导入
- `init_db()` 保证 staging group 存在（CREATE OR IGNORE）
- staging group 隔离：新入库账号进 staging，等待 x_digest eval

---

## [0.9.0] - 2026-03-01

### Added (S0007 — 查询模块)
- `src/db.py`：新增 5 个查询函数
  - `get_tweets(handle, since_hours, original_only)` — 按单账号查询
  - `search_tweets(query, group_name, since_hours, original_only)` — 关键词全文搜索（支持可选 group 范围限定）
  - `get_tweets_with_media(group_name, since_hours)` — 含媒体推文（JOIN media 表）
  - `get_quote_tweets(group_name, since_hours)` — Quote tweets（`quoted_tweet_id IS NOT NULL`）
  - `get_top_tweets(group_name, since_hours, limit, metric, original_only)` — Top N，metric 白名单防 SQL 注入
- 所有新接口使用 `fetched_at` 做时间过滤（ISO 8601，SQLite datetime 兼容）

### Added (S0008 — 每日导出)
- 新建 `src/exporter.py`
  - `export_group_to_json(group_name, since_hours, original_only)` — 单 group 导出，LEFT JOIN media + GROUP_CONCAT 聚合 URL
  - `export_all_groups(since_hours, output_dir)` — 导出所有 group 到 `data/exports/YYYY-MM-DD/<group>.json`
- `src/scheduler.py`：注册 `daily_export` cron job（每日 06:00，`max_instances=1` + `coalesce=True`）
- `DATABASE.md`：更新 Python 调用接口章节，新增 S0007/S0008 使用示例

---

## [0.7.0] - 2026-03-01

### Added (S0004 — Quote Tweet 展开)
- `tweets` 表新增 3 列：`quoted_tweet_id`, `quoted_full_text`, `quoted_author_handle`
- `src/db.py`：`init_db()` 新增 ALTER TABLE migration（兼容已有 DB）
- `src/db.py`：`insert_tweets()` INSERT 语句包含新列
- `src/x_api.py`：`_parse_tweet()` 从 `quoted_status_result.result` 提取被引用推文数据

### Added (S0005 — 媒体附件记录)
- 新建 `media` 表（`id`, `tweet_id`, `media_type`, `url`, `video_url`）
- `src/db.py`：`insert_media(media_items)` 批量插入函数
- `src/db.py`：`insert_tweets()` 在同一事务内联插入 media 记录
- `src/x_api.py`：`_parse_tweet()` 从 `extended_entities.media[]` 提取媒体附件，视频取最高码率 mp4
- `DATABASE.md`：更新 tweets 表说明，新增 media 表说明及关系图

---

## [0.6.0] - 2026-02-26

### Added
- `watched_accounts` 表新增 `source TEXT DEFAULT 'manual'` 列（含 ALTER TABLE migration，支持已有 DB 升级）
- `src/db.py`：`sync_from_list(handles)` — 从 X List 同步账号，自动 add/remove `source='list_sync'` 账号
- `src/x_api.py`：`get_list_members(list_id)` — 读取 X List 成员（GraphQL ListMembers，分页）
- `src/config.py`：`X_LIST_ID`（留空则跳过 List 同步）
- `src/scheduler.py`：`sync_watched_list()` + 每日 00:05 cron job（仅 X_LIST_ID 非空时注册）
- `main.py`：启动时调用 `sync_watched_list()`
- `cli.py`：`account list` 输出新增 `source` 列
- `.env.example`：新增 `X_LIST_ID=` 配置示例
- `docs/features/account-sync/overview.md` + `test-guide.md`

### Notes
- `QUERY_ID_LIST_MEMBERS` 需用户自行抓包填写（见 docs/features/account-sync/overview.md）

---

## [0.5.0] - 2026-02-26

### Changed
- `src/scheduler.py`：`fetch_all` job 新增 `max_instances=1`（防 cycle 重叠）和 `coalesce=True`（积压触发只跑一次）
- `.env.example`：`POLL_INTERVAL_MINUTES` 默认值从 30 改为 60（适配 100+ 账号串行采集场景）

### Added
- `docs/features/scheduler/overview.md`：scheduler 功能说明，含防重叠机制描述
- `docs/features/scheduler/test-guide.md`：防重叠验证步骤
- `stories/S0010-scheduler-stability.md`

---

## [0.4.0] - 2026-02-26

### Added
- `src/db.py`：`degrade_old_raw_json(days)` — 将超过 N 天的推文 `raw_json` 置 NULL，结构化字段永久保留
- `src/scheduler.py`：每日凌晨 3 点维护 job (`run_maintenance`)，自动触发 raw_json 降级
- `src/config.py`：`RAW_JSON_RETENTION_DAYS`（默认 90 天）
- `.env.example`：新增 `RAW_JSON_RETENTION_DAYS` 配置项
- `DATABASE.md`：面向下游 agent/项目的 DB 结构参考文档（表结构、关系图、Python 调用接口、生命周期说明）

---

## [0.3.0] - 2026-02-26

### Added
- `src/health.py`：`FailureTracker` 类 + `send_telegram_alert()`
- `src/scheduler.py`：集成健康检测，fetch_account 返回 bool；第 1 次 cycle 失败自动 refresh session；连续 3 次失败发 Telegram 告警后计数归零
- `src/config.py`：新增 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `HEALTH_ALERT_THRESHOLD`
- `.env.example`：新增 Telegram 配置示例

---

## [0.2.0] - 2026-02-26

### Added
- `account_groups` 和 `account_group_members` 表（多对多，幂等建表）
- `cli.py`：命令行工具，支持 `account add/remove/list` 和 `group create/assign/unassign/list/show/delete`
- `src/db.py` 新增函数：`add_watched_account`, `remove_watched_account`, `create_group`, `assign_to_group`, `unassign_from_group`, `get_groups`, `get_group_members`, `get_tweets_by_group`
- `get_tweets_by_group(group_name, since_hours, original_only)` 下游查询接口

---

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
