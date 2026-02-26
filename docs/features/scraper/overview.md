# x_scraper 功能说明
# Last Updated: 2026-02-26

## 这是什么

定时从 X（Twitter）抓取指定账号的推文，存入本地 SQLite 数据库。

作为**数据采集层**，供其他项目（每日行情摘要、AI 资讯聚合等）直接查询，不做任何分析或展示。

## 它做什么

1. 启动时读取 `cookies/cookies.json`（你导出的 X 登录态）
2. 首次运行立即抓取所有 watched accounts 的推文
3. 之后每 30 分钟自动增量抓取（只存新推文，已有的跳过）
4. 数据存在 `data/tweets.db`

## 数据库结构

| 字段 | 说明 |
|------|------|
| id | 推文 ID（主键，X 的 snowflake ID） |
| author_handle | 账号名，如 `elonmusk` |
| full_text | 推文正文 |
| created_at | 发推时间（X 原始格式） |
| is_retweet | 1=转推，0=原创/回复 |
| like_count / retweet_count / reply_count | 互动数据 |
| raw_json | X API 返回的原始 JSON（保留备用） |

## 查询示例

```python
import sqlite3, json

conn = sqlite3.connect('data/tweets.db')

# 获取某账号最新原创推文（排除转推和回复）
rows = conn.execute('''
    SELECT full_text, created_at, like_count
    FROM tweets
    WHERE author_handle = 'elonmusk'
      AND is_retweet = 0
    ORDER BY id DESC
    LIMIT 20
''').fetchall()
```

## 配置账号

编辑 `.env` 文件：
```
WATCHED_ACCOUNTS=elonmusk,sama,karpathy,lexfridman
```

重启服务生效。
