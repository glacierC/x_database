# S0013 - Article 推文内容补全（Jina Reader）

**状态**: Done
**创建**: 2026-03-07
**完成**: 2026-03-07

---

## 目标

当监听账号发布 X Article 时，自动通过 Jina Reader 抓取全文，存入 `article_content` 表。
现状：article 推文的 `full_text` 只有一个 t.co 短链，正文完全丢失。

---

## 验收标准

- [ ] 发现 article 推文时，`tweets.is_article = 1`，`full_text` 填充为 `title + preview_text`
- [ ] `article_content` 表新建，fetch_status 流转：`pending → ok / failed`
- [ ] 新增 scheduler job（每 30 分钟）：拉取 `pending` 的 article，调 Jina，写回结果
- [ ] Jina 失败时记录 `error_msg`，不崩溃，下次 cycle 重试（最多 3 次后标 `failed`）
- [ ] `search_tweets()` 能搜到 article 正文（通过 JOIN article_content）
- [ ] 存量 article 推文（raw_json 未降级的）可一次性 backfill

---

## DB 结构变更

### tweets 表：新增 1 列（migration）
```sql
ALTER TABLE tweets ADD COLUMN is_article INTEGER DEFAULT 0;
```

### 新建 article_content 表
```sql
CREATE TABLE IF NOT EXISTS article_content (
    tweet_id     TEXT PRIMARY KEY REFERENCES tweets(id),
    title        TEXT,
    content      TEXT,          -- Jina 返回的 markdown 全文
    fetch_status TEXT DEFAULT 'pending',  -- pending / ok / failed
    fetched_at   TEXT,
    error_msg    TEXT           -- 失败原因
);
```

### 生命周期
- `article_content` 不参与 raw_json 90 天降级，长期保留
- 如需清理，单独策略（当前不做）

---

## 涉及文件

| 文件 | 改动 |
|------|------|
| `src/db.py` | init_db() 加 migration + article_content CRUD |
| `src/x_api.py` | `_parse_tweet()` 检测 article 节点，填 is_article + 改写 full_text |
| `src/jina_fetcher.py` | 新建：构造 article URL + 调 `r.jina.ai` + 解析返回 |
| `src/scheduler.py` | 新增 job：每 30 分钟跑 pending article fetch |
| `src/db.py` | 新增 `get_pending_articles()` / `update_article_content()` |

---

## Article URL 构造逻辑

```
raw_json.article.article_results.result.rest_id  →  article 数字 ID
author_handle                                     →  用户名

article URL = https://x.com/<handle>/articles/<rest_id>
jina URL    = https://r.jina.ai/https://x.com/<handle>/articles/<rest_id>
```

注：`rest_id` 在 `raw_json` 里，**不需要跟随 t.co 跳转**，可直接构造。

---

## 存储规模估算

| 项目 | 估算 |
|------|------|
| 月均 article 数 | ~300 篇（112 账号 × 1% × 30天 × 平均推文量） |
| 单篇内容大小 | ~10 KB（Jina markdown） |
| 月增量 | ~3 MB |
| 年增量 | ~36 MB |

SQLite 无压力，不需要额外存储策略。

---

## Jina 限流说明

- Jina Reader 免费 tier：200 RPM
- 预计峰值：<10 articles/30min cycle，远低于限制
- 无需 API key（公开端点）

---

## 验收记录

（完成后填写）
