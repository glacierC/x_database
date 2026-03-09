# x_database Roadmap
# Last Updated: 2026-03-09

## 项目定位
X 推文定时采集服务。作为独立数据源，供下游分析项目（如每日信息摘要、市场事件追踪）直接查询 SQLite DB，无需重复爬取。

不负责分析，不负责展示，只负责**把指定账号的高质量推文持续、可靠地存进来**。

---

## ⚠️ 架构约束（2026-03-09 确认）

**无头浏览器采集上限：~1300 条推文/小时**

- 串行采集：每账号 ~6s，并发会更快触发 429
- X rate limit：429 触发后封禁 ~10 分钟窗口
- 付费 X API 方案评估：1000 账号 × 3 推文/小时 = 216 万条/月，Enterprise 起步 $3,500/月，性价比极差

**当前策略决定：**
- 维持无头浏览器方案，聚焦 **200-250 个高质量账号**
- crypto 和 staging 分组已清除（2026-03-09），当前 212 账号
- staging → eval → promote 自动化流程（S0014/S0015）代码保留，**执行暂停**（staging 已无账号，扩展需求未明确）

---

## ✅ 已完成

| Story | 描述 | 完成时间 |
|-------|------|---------|
| S0001 | 核心采集：Playwright cookie 管理 + X GraphQL API + SQLite 存储 + APScheduler 轮询 | 2026-02-26 |
| S0002 | Session 健康检测：失败自动 refresh，连续 3 次发 Telegram 告警 | 2026-02-26 |
| S0006 | 账号管理 CLI + Groups 多对多分组机制 + `get_tweets_by_group()` 查询接口 | 2026-02-26 |
| S0009 | 数据生命周期：raw_json 90 天自动降级（每日 3 点维护 job）+ DATABASE.md 文档 | 2026-02-26 |
| S0010 | Scheduler 稳定性：`max_instances=1` + `coalesce=True` 防 cycle 重叠，默认 interval 60 分钟 | 2026-02-26 |
| S0011 | Account 来源管理：X List 自动同步（source 字段、sync_from_list、每日 00:05 job） | 2026-02-26 |
| S0004 | Quote tweet 展开：tweets 表新增 3 列，`_parse_tweet()` 提取被引用推文数据 | 2026-03-01 |
| S0005 | 媒体附件记录：新建 media 表，提取图片/视频 URL（最高码率 mp4） | 2026-03-01 |
| S0007 | 查询模块：`get_tweets` / `search_tweets` / `get_tweets_with_media` / `get_quote_tweets` / `get_top_tweets` | 2026-03-01 |
| S0008 | 每日导出：`src/exporter.py` + 每日 06:00 cron job，导出 JSON 供下游消费 | 2026-03-01 |
| S0003 | 部署到 home-mac VPS：docker compose + volume 挂载 | 2026-03-03 |
| S0012 | 从 x_discovery 导入 YES 账号：112 个高质量信息源，按 ai_tech/macro/equities/geopolitics 分组 | 2026-03-04 |
| S0013 | Article 推文内容补全：via Jina reader 抓全文，存 article_content 表 | 2026-03-07 |
| S0014 | Staging 隔离 + 通用批量导入脚本（代码完成，流程已暂停） | 2026-03-08 |
| S0015 | 规范化导入 SOP + staging_eval 自动化（代码完成，流程已暂停） | 2026-03-08 |
| S0016 | Web Dashboard：Flask :8080，group 概览/账号状态/小时趋势，自动刷新 | 2026-03-09 |

---

## ⏸️ 暂停（代码保留，不执行）

| 功能 | 原因 |
|------|------|
| staging → eval → promote 自动化（S0014/S0015） | staging 已清空；采集上限下扩量性价比低；需求未明确 |
| crypto group 采集 | 已清除，363 账号不在监控范围 |

---

## 不在本项目范围内
- 推文分析、摘要生成 → 由独立分析项目实现
- 前端展示 → 不做（dashboard 仅监控运维用）
- 多用户支持 → 不做
