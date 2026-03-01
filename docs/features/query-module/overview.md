# 查询模块 — 功能说明
Last Updated: 2026-03-01

## 是什么

`src/db.py` 提供的一组 Python 函数，让下游项目无需写 SQL 即可查询推文数据。

## 给谁用

下游分析项目（如每日信息摘要、市场事件追踪），直接 import `src/db.py` 调用。

## 提供的函数

### `get_tweets(handle, since_hours, original_only)`
按单账号查询，无需指定 group。

```python
from src.db import get_tweets
tweets = get_tweets("karpathy", since_hours=48, original_only=True)
```

### `search_tweets(query, group_name, since_hours, original_only)`
全文关键词搜索（匹配 `full_text` 或 `quoted_full_text`）。`group_name` 可选，非 None 时限定范围。

```python
from src.db import search_tweets
results = search_tweets("LLM", group_name="ai", since_hours=72)
```

### `get_tweets_with_media(group_name, since_hours)`
返回指定 group 中含媒体附件（图片/视频）的推文。

```python
from src.db import get_tweets_with_media
media_tweets = get_tweets_with_media("ai", since_hours=24)
```

### `get_quote_tweets(group_name, since_hours)`
返回指定 group 中的 quote tweets（引用了其他推文的推文）。

```python
from src.db import get_quote_tweets
quotes = get_quote_tweets("ai", since_hours=48)
```

### `get_top_tweets(group_name, since_hours, limit, metric, original_only)`
按指定指标返回 Top N 推文。`metric` 可选 `like_count`、`retweet_count`、`reply_count`（非法值自动 fallback 到 `like_count`）。

```python
from src.db import get_top_tweets
top = get_top_tweets("ai", since_hours=24, limit=10, metric="like_count")
```

## 注意事项

- 时间过滤基于 `fetched_at`（ISO 8601 格式），而非 `created_at`（Twitter 非标准格式）
- 所有函数返回 `list[dict]`，每条 dict 包含 `tweets` 表所有字段
- 结果按 tweet id 倒序（最新在前），除 `get_top_tweets` 外
- `search_tweets` 使用 SQLite `LIKE`，对 ASCII 字母**大小写不敏感**（`"llm"` 和 `"LLM"` 结果相同）
- `get_tweets_with_media` 和 `get_quote_tweets` 依赖 S0004/S0005 migration（首次使用需先运行 `init_db()`）
