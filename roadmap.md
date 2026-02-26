# x_scraper Roadmap
# Last Updated: 2026-02-26 (S0011 完成)

## 项目定位
X 推文定时采集服务。作为独立数据源，供下游分析项目（如每日信息摘要、市场事件追踪）直接查询 SQLite DB，无需重复爬取。

不负责分析，不负责展示，只负责**把指定账号的高质量推文持续、可靠地存进来**。

---

## 当前版本：v0.1（基础采集）

### ✅ 已完成

| Story | 描述 | 完成时间 |
|-------|------|---------|
| S0001 | 核心采集：Playwright cookie 管理 + X GraphQL API + SQLite 存储 + APScheduler 30min 轮询 | 2026-02-26 |
| S0002 | Session 健康检测：失败自动 refresh，连续 3 次发 Telegram 告警 | 2026-02-26 |
| S0006 | 账号管理 CLI + Groups 多对多分组机制 + `get_tweets_by_group()` 查询接口 | 2026-02-26 |
| S0009 | 数据生命周期：raw_json 90 天自动降级（每日 3 点维护 job）+ DATABASE.md 文档 | 2026-02-26 |
| S0010 | Scheduler 稳定性：`max_instances=1` + `coalesce=True` 防 cycle 重叠，默认 interval 改为 60 分钟 | 2026-02-26 |
| S0011 | Account 来源管理：X List 自动同步（source 字段、sync_from_list、get_list_members、每日 00:05 job） | 2026-02-26 |

---

## v0.5（当前）：采集稳定性

目标：让 scraper 能长期无人值守跑，100+ 账号不重叠，session 失效自恢复。

| Story | 描述 | 状态 |
|-------|------|------|
| S0010 | Scheduler 稳定性：防 job 重叠（`max_instances=1` + `coalesce=True`），默认 interval 60 分钟 | ✅ Done |
| S0011 | Account 来源管理：X List 同步（source 字段 + sync_from_list + get_list_members + 定时 job） | ✅ Done |
| S0003 | 部署到 home-mac VPS：docker compose + volume 挂载，scp cookies 迁移 | Todo |

---

## 预留：高时效性账号（待需求明确后设计）

> 当前不实现。等用户明确交易信号链路后再规划。

技术方向：独立 scheduler + 快速 poll group（5 分钟间隔），与主 cycle 隔离。

---

## v0.3：数据质量提升

目标：让存入 DB 的数据更完整，方便下游消费。

| Story | 描述 | 状态 |
|-------|------|------|
| S0004 | Quote tweet 展开：存储被引用原推的全文（现在只存了引用者的文本） | Todo |
| S0005 | 媒体附件记录：图片/视频 URL 存入 media 表 | Todo |
| S0006 | 账号管理 CLI：命令行 add/remove watched accounts，不用手改 .env | ✅ Done (移至已完成) |

---

## v1.0：对外查询接口（数据消费层，后续再做）

目标：给下游项目提供简洁的 Python 接口，屏蔽 SQL 细节。

| Story | 描述 | 状态 |
|-------|------|------|
| S0007 | 查询模块：`get_tweets(handle, since, original_only)` 等常用接口 | Todo |
| S0008 | 每日摘要导出：按时间窗口导出指定账号的原创推文为 JSON，供分析项目消费 | Todo |

---

## 不在本项目范围内
- 推文分析、摘要生成 → 由独立分析项目实现
- 前端展示 → 不做
- 多用户支持 → 不做
