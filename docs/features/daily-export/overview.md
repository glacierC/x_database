# 每日导出 — 功能说明
Last Updated: 2026-03-01

## 是什么

每日自动将所有 group 的推文导出为 JSON 文件，供下游分析项目直接读取，无需连接数据库。

## 给谁用

下游分析项目（如每日摘要生成器），直接读取 JSON 文件消费数据。

## 文件位置

```
data/exports/
└── YYYY-MM-DD/
    ├── ai.json
    ├── markets.json
    └── macro.json
```

每个 JSON 文件是一个数组，每条记录包含：

| 字段 | 说明 |
|------|------|
| `id` | 推文 ID |
| `author_handle` | 作者 handle |
| `full_text` | 推文全文 |
| `created_at` | 发推时间 |
| `like_count` | 点赞数 |
| `retweet_count` | 转推数 |
| `reply_count` | 回复数 |
| `is_retweet` | 1 = 转推 |
| `quoted_tweet_id` | 被引用推文 ID（可为 null） |
| `quoted_author_handle` | 被引用推文作者（可为 null） |
| `quoted_full_text` | 被引用推文正文（可为 null） |
| `media_urls` | 媒体 URL 列表（无媒体时为 `[]`） |

## 执行时间

每日 **06:00**（本地时间，scheduler 所在机器）自动执行，导出过去 24 小时数据。

## 手动触发

```python
from src.exporter import export_all_groups
result = export_all_groups(since_hours=24, output_dir="data/exports")
print(result)  # {group_name: file_path}
```
