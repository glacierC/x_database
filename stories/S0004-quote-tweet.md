# S0004 — Quote Tweet 展开

**状态**: Done
**完成时间**: 2026-03-01

---

## 目标

存储 quote tweet 中被引用原推的完整内容，而不仅仅是引用者的文字。

---

## 验收标准

- [ ] `tweets` 表新增 3 列：`quoted_tweet_id`、`quoted_full_text`、`quoted_author_handle`
- [ ] 已有 DB 通过 ALTER TABLE migration 自动升级，无需重建
- [ ] `_parse_tweet()` 从 `result.quoted_status_result.result` 路径提取被引用推文数据
- [ ] 验证：`SELECT author_handle, quoted_author_handle, quoted_full_text FROM tweets WHERE quoted_tweet_id IS NOT NULL LIMIT 5;` 有数据

---

## 涉及文件

- `src/db.py`：migration + INSERT 语句更新
- `src/x_api.py`：`_parse_tweet()` 提取 quote tweet 字段
- `DATABASE.md`：tweets 表文档更新

---

## 验收记录

**API 字段路径（已从线上 DB raw_json 验证）：**
- `result.quoted_status_result.result.rest_id` → quoted_tweet_id
- `result.quoted_status_result.result.legacy.full_text` → quoted_full_text
- `result.quoted_status_result.result.core.user_results.result.legacy.screen_name` → quoted_author_handle

实现完成，已通过代码审查。等下一个 poll cycle 抓取 quote tweet 后可验证数据填充。
