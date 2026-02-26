# 账号管理 + Groups 功能
# Last Updated: 2026-02-26

## 是什么

让你不用手改 `.env` 就能增删监控账号，并把账号按话题分组（如 "ai"、"markets"），方便下游项目按组查数据。

## 给谁用

- 你自己：用 CLI 日常维护监控列表
- 下游 Python 项目：调用 `get_tweets_by_group()` 按组拉推文

---

## 账号管理

```bash
python cli.py account add karpathy sama lexfridman   # 添加
python cli.py account remove karpathy               # 删除（同时清理 group 关联）
python cli.py account list                          # 查看全部
```

> `account add` 同时支持 `@karpathy` 和 `karpathy` 两种格式。

---

## Group 管理

```bash
python cli.py group create ai "AI researchers and builders"
python cli.py group assign ai karpathy sama lexfridman
python cli.py group unassign ai sama
python cli.py group show ai
python cli.py group list
python cli.py group delete ai
```

---

## 下游查询接口

```python
from src.db import get_tweets_by_group

# 获取 "ai" 组过去 24 小时的原创推文（不含转推）
tweets = get_tweets_by_group("ai", since_hours=24, original_only=True)

# 每条推文是一个 dict，包含：
# id, author_handle, full_text, created_at, like_count, is_retweet, ...
```

---

## DB 结构

```
account_groups              account_group_members       watched_accounts
──────────────              ─────────────────────       ────────────────
name (PK)              ◄──  group_name                  handle (PK)
description                 handle              ──────► handle
```

一个账号可同时属于多个 group（多对多）。
