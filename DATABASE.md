# x_database — Database Reference
# Last Updated: 2026-03-01 (S0007 + S0008 查询模块 & 每日导出)
# 给下游 agent / 项目调用时参考此文档

---

## 概述

SQLite 数据库，默认路径：`./data/tweets.db`（可通过 `DB_PATH` 环境变量覆盖）。

用途：存储指定 X (Twitter) 账号的推文，供下游分析项目查询，不对外暴露任何 API。

---

## 表结构

### `tweets` — 推文主表

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PK | 推文 ID（X 内部数字 ID，字符串形式） |
| `author_id` | TEXT | 作者数字 ID |
| `author_handle` | TEXT | 作者 handle（如 `karpathy`，不含 @） |
| `full_text` | TEXT | 推文全文（含转推前缀 `RT @...`） |
| `created_at` | TEXT | 发推时间，Twitter 原始格式：`Wed Feb 26 10:00:00 +0000 2026` |
| `retweet_count` | INTEGER | 转推数 |
| `like_count` | INTEGER | 点赞数 |
| `reply_count` | INTEGER | 回复数 |
| `is_retweet` | INTEGER | 1 = 转推，0 = 原创 |
| `quoted_tweet_id` | TEXT \| NULL | 被引用推文 ID（仅 quote tweet 有值） |
| `quoted_full_text` | TEXT \| NULL | 被引用推文正文 |
| `quoted_author_handle` | TEXT \| NULL | 被引用推文作者 handle |
| `raw_json` | TEXT \| NULL | X GraphQL 原始响应 JSON。**90 天后自动降级为 NULL**，结构化字段永久保留 |
| `fetched_at` | TEXT | 抓取时间，ISO 8601 格式：`2026-02-26T10:00:00.000000+00:00` |

**注意**：`created_at` 是 Twitter 非标准格式，不能直接用 SQLite `datetime()` 比较。如需按时间过滤，请在 Python 侧解析，或使用 `fetched_at`（ISO 格式，可直接用 SQLite datetime 函数）。

---

### `watched_accounts` — 监控账号表

| 列名 | 类型 | 说明 |
|------|------|------|
| `handle` | TEXT PK | 账号 handle（如 `karpathy`） |
| `user_id` | TEXT | X 内部数字 ID（首次抓取后填入） |
| `last_fetched_at` | TEXT | 最后成功抓取时间，ISO 8601 |

---

### `media` — 媒体附件表

| 列名 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PK | 媒体资源 ID（X 内部 `id_str`） |
| `tweet_id` | TEXT | 关联推文 ID |
| `media_type` | TEXT | 类型：`photo` / `video` / `animated_gif` |
| `url` | TEXT | 媒体静态图 URL（`media_url_https`） |
| `video_url` | TEXT \| NULL | 最高码率 mp4 URL（仅 video/gif 有值） |

---

### `account_groups` — 分组定义表

| 列名 | 类型 | 说明 |
|------|------|------|
| `name` | TEXT PK | 组名（如 `ai`、`markets`、`macro`） |
| `description` | TEXT | 描述（可为空） |

---

### `account_group_members` — 账号↔分组关联（多对多）

| 列名 | 类型 | 说明 |
|------|------|------|
| `group_name` | TEXT | 外键 → `account_groups.name` |
| `handle` | TEXT | 外键 → `watched_accounts.handle` |
| PK | — | `(group_name, handle)` 联合主键 |

一个账号可同时属于多个 group。

---

## 关系图

```
account_groups          account_group_members        watched_accounts
──────────────          ─────────────────────        ────────────────
name (PK)          ◄──  group_name                   handle (PK)
description             handle               ──────► handle
                                                      user_id
                                                      last_fetched_at
                              │
                              ▼
                           tweets                          media
                        ──────────────                ──────────────
                        id (PK)              ◄──────  tweet_id
                        author_handle ◄── (JOIN)      id (PK)
                        full_text                     media_type
                        created_at                    url
                        is_retweet                    video_url
                        like_count
                        quoted_tweet_id
                        quoted_full_text
                        quoted_author_handle
                        raw_json (90天后 NULL)
                        fetched_at
```

---

## Python 调用接口

直接 import `src/db.py` 使用，**不需要写 SQL**。

```python
from src.db import (
    get_watched_accounts,       # 获取所有监控账号
    get_group_members,          # 获取某 group 的所有 handle
    get_tweets_by_group,        # 按 group 查询（基础接口）
    # S0007 扩展查询接口
    get_tweets,                 # 按单账号查询
    search_tweets,              # 关键词全文搜索
    get_tweets_with_media,      # 含媒体推文
    get_quote_tweets,           # Quote tweets
    get_top_tweets,             # Top N 推文
)
```

### `get_tweets_by_group(group_name, since_hours, original_only)`

```python
from src.db import get_tweets_by_group

tweets = get_tweets_by_group(
    group_name="ai",        # group 名称
    since_hours=24,         # 只看最近 N 小时（基于 created_at 近似）
    original_only=True,     # True = 过滤转推，只返回原创
)

# 每条是 dict，包含所有 tweets 表字段
# tweets[0]["full_text"]
# tweets[0]["author_handle"]
# tweets[0]["like_count"]
# tweets[0]["raw_json"]  # 可能为 None（90天后自动清空）

# 结果按 tweet id 倒序（最新在前）
```

### S0007 扩展查询接口

```python
from src.db import get_tweets, search_tweets, get_tweets_with_media, get_quote_tweets, get_top_tweets

# 按单账号查（不需要指定 group）
tweets = get_tweets("karpathy", since_hours=48, original_only=True)

# 关键词搜索（group_name 可选）
results = search_tweets("LLM", group_name="ai", since_hours=72)

# 含媒体推文
media_tweets = get_tweets_with_media("ai", since_hours=24)

# Quote tweets
quotes = get_quote_tweets("ai", since_hours=48)

# Top N（metric: like_count | retweet_count | reply_count）
top = get_top_tweets("ai", since_hours=24, limit=10, metric="like_count")
```

**注意**：S0007 接口时间过滤基于 `fetched_at`（ISO 8601），可直接用 SQLite `datetime()` 比较。

### S0008 每日导出接口

```python
from src.exporter import export_all_groups, export_group_to_json

# 导出所有 group → data/exports/YYYY-MM-DD/<group>.json
result = export_all_groups(since_hours=24)
# result: {"ai": "data/exports/2026-03-01/ai.json", ...}

# 单 group 导出为 list[dict]（含 media_urls 列表字段）
tweets = export_group_to_json("ai", since_hours=24)
# tweets[0]["media_urls"]  →  ["https://..."] 或 []
```

### 直接查询示例

```python
import sqlite3, os
conn = sqlite3.connect(os.getenv("DB_PATH", "./data/tweets.db"))
conn.row_factory = sqlite3.Row

# 某 group 过去 48 小时原创推文（用 fetched_at 过滤，ISO 格式更可靠）
rows = conn.execute("""
    SELECT t.author_handle, t.full_text, t.like_count, t.fetched_at
      FROM tweets t
      JOIN account_group_members m ON t.author_handle = m.handle
     WHERE m.group_name = 'ai'
       AND t.is_retweet = 0
       AND t.fetched_at >= datetime('now', '-48 hours')
     ORDER BY t.id DESC
""").fetchall()
```

---

## 数据生命周期

| 阶段 | 时间 | raw_json | 其他字段 |
|------|------|----------|---------|
| 新入库 | 0–90 天 | ✅ 完整 JSON | ✅ 保留 |
| 降级 | 90 天后 | ❌ 自动置 NULL | ✅ 永久保留 |

降级由每日凌晨 3 点的维护 job 执行，阈值通过 `RAW_JSON_RETENTION_DAYS` 配置（默认 90）。

---

## 典型 Group 用法

```bash
# 配置 group（一次性，之后不用改）
python cli.py group create ai "AI researchers"
python cli.py group assign ai karpathy sama lexfridman

# 下游项目直接查
from src.db import get_tweets_by_group
tweets = get_tweets_by_group("ai", since_hours=24, original_only=True)
```
