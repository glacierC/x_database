# x_scraper Roadmap
# Last Updated: 2026-03-03 (S0003 完成，VPS 部署 Done)

## 项目定位
X 推文定时采集服务。作为独立数据源，供下游分析项目（如每日信息摘要、市场事件追踪）直接查询 SQLite DB，无需重复爬取。

不负责分析，不负责展示，只负责**把指定账号的高质量推文持续、可靠地存进来**。

---

## ✅ 已完成

| Story | 描述 | 完成时间 |
|-------|------|---------|
| S0001 | 核心采集：Playwright cookie 管理 + X GraphQL API + SQLite 存储 + APScheduler 30min 轮询 | 2026-02-26 |
| S0002 | Session 健康检测：失败自动 refresh，连续 3 次发 Telegram 告警 | 2026-02-26 |
| S0006 | 账号管理 CLI + Groups 多对多分组机制 + `get_tweets_by_group()` 查询接口 | 2026-02-26 |
| S0009 | 数据生命周期：raw_json 90 天自动降级（每日 3 点维护 job）+ DATABASE.md 文档 | 2026-02-26 |
| S0010 | Scheduler 稳定性：`max_instances=1` + `coalesce=True` 防 cycle 重叠，默认 interval 60 分钟 | 2026-02-26 |
| S0011 | Account 来源管理：X List 自动同步（source 字段、sync_from_list、get_list_members、每日 00:05 job） | 2026-02-26 |
| S0004 | Quote tweet 展开：tweets 表新增 3 列，`_parse_tweet()` 提取被引用推文数据 | 2026-03-01 |
| S0005 | 媒体附件记录：新建 media 表，提取图片/视频 URL（最高码率 mp4） | 2026-03-01 |
| S0007 | 查询模块：`get_tweets` / `search_tweets` / `get_tweets_with_media` / `get_quote_tweets` / `get_top_tweets` | 2026-03-01 |
| S0008 | 每日导出：`src/exporter.py` + 每日 06:00 cron job，导出 JSON 供下游消费 | 2026-03-01 |

---

## ✅ v0.5 采集稳定性（已全部完成）

| Story | 描述 | 状态 |
|-------|------|------|
| S0003 | 部署到 home-mac VPS：docker compose + volume 挂载，scp cookies 迁移 | ✅ Done (2026-03-03) |

---

## ✅ v1.1 信息源批量导入（已完成）

| Story | 描述 | 状态 |
|-------|------|------|
| S0012 | 从 x_discovery 导入 YES 账号：112 个高质量信息源，按 ai_tech/macro/equities/geopolitics 分组 | ✅ Done (2026-03-04) |

---

## 当前：无待办

> v1.1 上线，监听账号 112 个（x_discovery 评估 YES）+ 已有账号，持续运行中。

---

## 预留：高时效性账号（待需求明确后设计）

> 当前不实现。等用户明确交易信号链路后再规划。

技术方向：独立 scheduler + 快速 poll group（5 分钟间隔），与主 cycle 隔离。

---

## 不在本项目范围内
- 推文分析、摘要生成 → 由独立分析项目实现
- 前端展示 → 不做
- 多用户支持 → 不做
