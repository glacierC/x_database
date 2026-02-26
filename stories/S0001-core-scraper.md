# S0001 - 核心推文采集
# Status: Done
# Completed: 2026-02-26

## 目标
搭建最小可用的推文采集服务：用 Playwright 维护 X session，通过内部 GraphQL API 抓取指定账号推文，存入 SQLite，30 分钟轮询一次。

## 验收标准
- [x] `python main.py` 启动后自动完成首次抓取
- [x] `sqlite3 data/tweets.db "SELECT count(*) FROM tweets"` 返回 > 0
- [x] 重复运行不重复存储（INSERT OR IGNORE）
- [x] 支持多账号（WATCHED_ACCOUNTS 逗号分隔）
- [x] Dockerfile + docker-compose 可构建

## 涉及文件
- `main.py` — 入口
- `src/config.py` — 环境变量配置
- `src/auth.py` — cookie 管理 + token 提取
- `src/x_api.py` — X GraphQL 客户端
- `src/db.py` — SQLite init + CRUD
- `src/scheduler.py` — APScheduler 轮询
- `Dockerfile`, `docker-compose.yml`

## 验收记录
- 成功抓取 elonmusk(192)、sama(155)、karpathy(118)，共 465 条推文
- 发现并修复 bug：`get_latest_tweet_id` 按文本排序 created_at 导致漏抓（改为按 tweet ID 排序）
- cookies.json 直读 token，无需每次启动 Playwright
