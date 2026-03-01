# x_database — 下游项目接入指南
Last Updated: 2026-03-01

> 本文档面向**调用方项目**（如每日摘要、市场追踪等）。
> 你不需要理解 x_database 的内部实现，按本文选择接入方式即可。

---

## 数据是什么

定时抓取的 X (Twitter) 推文库。当前收录账号分组：

| Group | 用途 |
|-------|------|
| `ai` | AI 研究者、从业者 |

> 查看所有 group：`python cli.py group list`（需在 x_database 目录执行）

数据每 60 分钟自动更新，每日 06:00 自动导出 JSON 快照。

---

## 接入方式

### ✅ 方式一：读取每日 JSON 快照（推荐）

**适合**：每日批量分析、不需要实时数据、零依赖

每日 06:00 自动生成快照，路径格式：

```
<x_database_root>/data/exports/YYYY-MM-DD/<group>.json
```

```python
import json
from pathlib import Path
from datetime import date

exports_dir = Path("/path/to/x_database/data/exports")
today = date.today().isoformat()

data = json.loads((exports_dir / today / "ai.json").read_text())

for tweet in data:
    print(tweet["author_handle"], tweet["full_text"][:80])
    print("  ❤️", tweet["like_count"], "🔁", tweet["retweet_count"])
    if tweet["media_urls"]:
        print("  📎", tweet["media_urls"])
```

**每条记录的字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | str | 推文 ID |
| `author_handle` | str | 作者 handle（不含 @） |
| `full_text` | str | 推文全文 |
| `created_at` | str | 发推时间（Twitter 原始格式，仅供展示） |
| `like_count` | int | 点赞数 |
| `retweet_count` | int | 转推数 |
| `reply_count` | int | 回复数 |
| `is_retweet` | int | 1 = 转推，0 = 原创 |
| `quoted_tweet_id` | str \| null | 被引用推文 ID |
| `quoted_author_handle` | str \| null | 被引用推文作者 |
| `quoted_full_text` | str \| null | 被引用推文正文 |
| `media_urls` | list[str] | 媒体图片/视频 URL，无媒体时为 `[]` |

---

### ✅ 方式二：直接查询 SQLite（灵活，仅需标准库）

**适合**：需要自定义过滤条件、实时读取最新数据

```python
import sqlite3

DB_PATH = "/path/to/x_database/data/tweets.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# 过去 24 小时 ai group 的原创推文
rows = conn.execute("""
    SELECT t.author_handle, t.full_text, t.like_count,
           t.quoted_full_text, t.fetched_at
      FROM tweets t
      JOIN account_group_members m ON t.author_handle = m.handle
     WHERE m.group_name = 'ai'
       AND t.is_retweet = 0
       AND t.fetched_at >= datetime('now', '-24 hours')
     ORDER BY t.id DESC
""").fetchall()

for r in rows:
    print(dict(r))
```

**关键提示：**
- 用 `fetched_at`（ISO 8601）做时间过滤，**不要用 `created_at`**（Twitter 非标格式，无法直接比较）
- 数据库为只读使用，请勿写入

---

### ⚙️ 方式三：import Python 接口（功能最全）

**适合**：与 x_database 在同一机器、需要关键词搜索或 Top N 等高级查询

**前提**：将 x_database 根目录加入 Python 路径，并安装其依赖。

```bash
# 安装依赖（在 x_database 目录）
pip install -r requirements.txt
```

```python
import sys
sys.path.insert(0, "/path/to/x_database")

import os
os.environ["DB_PATH"] = "/path/to/x_database/data/tweets.db"

from src.db import (
    get_tweets_by_group,      # 按 group 查最近 N 小时推文
    get_tweets,               # 按单账号查
    search_tweets,            # 关键词全文搜索（大小写不敏感）
    get_top_tweets,           # Top N（按点赞/转推/回复数排序）
    get_tweets_with_media,    # 仅含媒体附件的推文
    get_quote_tweets,         # 仅 quote tweets
)

# 示例
tweets = get_tweets_by_group("ai", since_hours=24, original_only=True)
top    = get_top_tweets("ai", since_hours=24, limit=10, metric="like_count")
found  = search_tweets("LLM", group_name="ai", since_hours=72)
```

**所有函数返回 `list[dict]`，每条包含 tweets 表的全部字段（不含 `media_urls`，需用方式一或方式二获取）。**

---

## 选择建议

| 场景 | 推荐方式 |
|------|---------|
| 每日定时跑批分析 | 方式一（JSON 快照） |
| 需要实时最新数据 | 方式二（SQLite 直查） |
| 需要关键词搜索 / Top N | 方式三（Python 接口） |
| 下游是非 Python 项目 | 方式一（JSON 快照） |

---

## 注意事项

- **只读**：下游项目不应向 DB 写入任何数据
- **`raw_json` 字段**：90 天后自动清空，不要依赖它
- **`created_at` 格式**：Twitter 原始格式（`Wed Feb 26 10:00:00 +0000 2026`），仅用于展示，时间过滤请用 `fetched_at`
- **快照时间**：JSON 快照每日 06:00 生成，包含过去 24 小时数据；当天更早的数据用方式二直查
