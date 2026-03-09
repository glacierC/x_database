Last Updated: 2026-03-09

# x_database — 排障记录

---

## BUG-001 · 容器每 10 分钟重启，只有前几个账号被采集

**现象：** 容器日志显示 `Starting x_scraper` 每约 10 分钟出现一次，868 个账号中只有排在最前面的 5-15 个账号有推文记录，其余 `last_fetched_at = NULL`。

**根本原因：**
`_api_get` 在收到 429 (rate limited) 时，在 API 调用内部原地 `await asyncio.sleep(675)`，把整个账号 fetch cycle 阻塞长达 10+ 分钟。每次容器重启后从第一个账号重头开始，导致同一批账号反复触发 429，形成死循环：

```
启动 → 抓前几个账号 → 触发 429 → 挂住 675s → 重启 → 重复
```

次要原因：`fetch_all_accounts` 在 cycle 出现失败时会触发 `refresh_session()`（Playwright/Chrome），但 503/429 是服务端限流，不是 auth 失败，不应启动 Chrome，浪费资源且可能引发内存压力。

**修复：**

1. `x_api.py`：429 改为抛出 `RateLimitError(reset_after)`，不再内联 sleep
2. `scheduler.py`：`fetch_account` 透传 `RateLimitError`；`fetch_all_accounts` 在 outer loop 捕获，sleep `reset_after` 秒后继续后续账号
3. `scheduler.py`：移除 `fail_count==1` 触发 `refresh_session()` 的逻辑

```python
# x_api.py — 修复前
await asyncio.sleep(wait)          # 原地阻塞 cycle
return await _api_get(...)         # 重试同一账号

# x_api.py — 修复后
raise RateLimitError(reset_after)  # 立即抛出，不阻塞

# scheduler.py — outer loop 统一处理
except RateLimitError as e:
    await asyncio.sleep(e.reset_after)  # 等 reset 窗口
    ok = False                          # 当前账号标记失败，下一轮重试
```

**行为变化：** 遇到 429 → 等 reset 窗口（60-675s）→ 继续剩余账号 → 被限流的账号下一个 cycle 自动重试。

**文件：** `src/x_api.py`、`src/scheduler.py`

---

## BUG-002 · staging eval 只评估了少数账号，大量账号 0 推文

**现象：** 将 365 个 crypto 账号移入 staging 后，48h staging_eval 只评估了 5 个账号，其余 325 个账号无推文记录（`last_fetched_at = NULL`）。

**根本原因：**
同 BUG-001。容器每 10 分钟重启，每次只抓到排在 `watched_accounts` 最前面的 10-15 个账号，大量账号从未被采集。这些账号在 `account_group_members` 中存在，但 `tweets` 表中没有任何记录，`get_staging_tweets()` 因此找不到可评估的推文。

**修复：** 同 BUG-001（解决容器重启问题后，下一个完整 cycle 会采集所有账号）。

**诊断查询：**
```python
# 查看 staging 账号推文覆盖情况
conn.execute("""
    SELECT
        CASE WHEN last_fetched_at IS NULL THEN 'never' ELSE 'fetched' END,
        COUNT(*)
    FROM watched_accounts wa
    JOIN account_group_members gm ON wa.handle = gm.handle
    WHERE gm.group_name = 'staging'
    GROUP BY 1
""")
```

---

## BUG-003 · OrbStack Docker daemon 无响应

**现象：** `docker ps` 无响应，`docker compose up` 卡住，SSH 后执行 docker 命令全部 EOF 错误。

**根本原因：** 多个项目同时执行 `docker compose up --build`，把 OrbStack Docker daemon 请求队列堵死（2026-03-09 复现）。

**急救：**
```bash
ssh home-mac "pkill -9 -f OrbStack; sleep 3; open -a OrbStack"
# 等待 15s OrbStack 重启
ssh home-mac "cd ~/services/x_database && ~/.orbstack/bin/docker compose up -d"
```

**预防：** 部署必须串行，一个项目 build 完再部署下一个。

---

## 常用诊断命令

```bash
# 查看容器状态
ssh home-mac "~/.orbstack/bin/docker ps --format 'table {{.Names}}\t{{.Status}}'"

# 查看 x_database 实时日志
ssh home-mac "~/.orbstack/bin/docker logs x_database-app-1 -f 2>&1"

# 查看容器重启次数
ssh home-mac "~/.orbstack/bin/docker inspect x_database-app-1 --format='RestartCount={{.RestartCount}} ExitCode={{.State.ExitCode}}'"

# 查看内存用量
ssh home-mac "~/.orbstack/bin/docker stats x_database-app-1 --no-stream"

# 查采集覆盖率（有推文 vs 从未采集）
# docker exec -i x_database-app-1 python3
import sqlite3
conn = sqlite3.connect('data/tweets.db')
print(conn.execute("SELECT COUNT(*) FROM watched_accounts WHERE last_fetched_at IS NOT NULL").fetchone())
print(conn.execute("SELECT COUNT(*) FROM watched_accounts WHERE last_fetched_at IS NULL").fetchone())

# 查 429 日志
ssh home-mac "~/.orbstack/bin/docker logs x_database-app-1 2>&1 | grep '429\|Rate limit'"

# 查某 group 账号推文覆盖情况
ssh home-mac "~/.orbstack/bin/docker logs x_database-app-1 2>&1 | grep CYCLE | tail -5"
```
