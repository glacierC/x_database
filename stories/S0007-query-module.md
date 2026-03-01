# S0007 — 查询模块
Last Updated: 2026-03-01

## 目标
在 `src/db.py` 新增 5 个查询函数，覆盖按单账号查、关键词搜索、含媒体、quote tweet、Top N 等下游消费场景。

## 状态：Done
完成时间：2026-03-01

## 验收标准
- [x] `get_tweets(handle, since_hours, original_only)` 可返回单账号推文列表
- [x] `search_tweets(query, group_name, since_hours, original_only)` 支持全文搜索，group_name 可选
- [x] `get_tweets_with_media(group_name, since_hours)` 返回含媒体推文（JOIN media 表）
- [x] `get_quote_tweets(group_name, since_hours)` 返回 `quoted_tweet_id IS NOT NULL` 的推文
- [x] `get_top_tweets(group_name, since_hours, limit, metric, original_only)` 按指定指标排序，metric 白名单防注入

## 涉及文件
- `src/db.py`（修改）
- `docs/features/query-module/overview.md`（新建）
- `docs/features/query-module/test-guide.md`（新建）

## 验收记录
所有函数已按 SQL 规范实现，`metric` 字段白名单校验防 SQL 注入，`fetched_at` 用于时间过滤（ISO 8601 格式，兼容 SQLite datetime）。
