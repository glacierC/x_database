# Scheduler — 功能说明

Last Updated: 2026-02-26

---

## 是什么

定时轮询所有 watched accounts，将新推文写入 SQLite DB。每隔固定时间（默认 60 分钟）自动触发一次抓取 cycle。

---

## 两个定时任务

| Job ID | 触发方式 | 描述 |
|--------|---------|------|
| `fetch_all` | 每 N 分钟（`POLL_INTERVAL_MINUTES`） | 串行抓取所有 watched accounts 的新推文 |
| `daily_maintenance` | 每天凌晨 3:00 | 清理超过 `RAW_JSON_RETENTION_DAYS` 天的 raw_json 字段 |

---

## 防重叠机制（v0.5.0 起）

`fetch_all` job 配置了：

- **`max_instances=1`**：同一时间只允许 1 个实例运行。若上一个 cycle 仍在进行，新 trigger 到达时不会启动第二个实例。
- **`coalesce=True`**：若错过了多次触发（如系统休眠），恢复后只补跑一次，不会连续补跑多次。

这两个参数共同保证：**100+ 账号串行抓取时，不会因 cycle 超时导致并行抓取，避免加剧 API rate limit 风险。**

---

## 配置项

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POLL_INTERVAL_MINUTES` | `60` | 两次抓取 cycle 之间的间隔（分钟） |
| `RAW_JSON_RETENTION_DAYS` | `90` | raw_json 保留天数（维护 job 使用） |

---

## 日志标志

- cycle 开始：`=== Poll cycle start ===`
- cycle 结束：`=== Poll cycle done ===`

正常运行时，两条日志交替出现，cycle done 一定早于下一个 cycle start。
