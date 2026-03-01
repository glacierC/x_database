# 查询模块 — 测试指南
Last Updated: 2026-03-01

## 前提

确保 DB 已有数据（至少运行过一次采集），并已配置好 group。

```bash
python cli.py group create ai "AI researchers"
python cli.py group assign ai karpathy
```

## 验证步骤

在项目根目录运行 Python（确保 `.env` 已加载或环境变量已设置）：

```python
import os; os.chdir("/path/to/x_database")
from src.db import get_tweets, search_tweets, get_tweets_with_media, get_quote_tweets, get_top_tweets

# 1. 按单账号查
tweets = get_tweets("karpathy", since_hours=48)
assert isinstance(tweets, list)
print(f"get_tweets: {len(tweets)} tweets")

# 2. 关键词搜索（SQLite LIKE 大小写不敏感，需用 .lower() 验证）
results = search_tweets("LLM", group_name="ai", since_hours=72)
assert all(
    "llm" in (r["full_text"] or "").lower() or "llm" in (r["quoted_full_text"] or "").lower()
    for r in results
)
print(f"search_tweets: {len(results)} results")

# 3. Top N
top = get_top_tweets("ai", since_hours=24, limit=5)
if len(top) >= 2:
    assert top[0]["like_count"] >= top[-1]["like_count"]
print(f"get_top_tweets: {len(top)} tweets")

# 4. Quote tweets
qt = get_quote_tweets("ai", since_hours=48)
assert all(r["quoted_tweet_id"] is not None for r in qt)
print(f"get_quote_tweets: {len(qt)} tweets")

# 5. 含媒体推文
media_tweets = get_tweets_with_media("ai", since_hours=24)
print(f"get_tweets_with_media: {len(media_tweets)} tweets")

print("All assertions passed ✓")
```

## 预期结果

- 所有 `assert` 通过，无报错
- 函数返回空列表是正常的（表示近期无符合条件数据）
