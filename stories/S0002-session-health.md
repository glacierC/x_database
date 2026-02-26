# S0002 — Session 健康检测
# Last Updated: 2026-02-26

## 状态：Done
## 完成时间：2026-02-26

---

## 目标

让 scraper 在 session 失效时能自动恢复，连续失败时发 Telegram 通知，不需要人工盯着看日志。

---

## 验收标准

- [ ] 单次抓取失败 → 自动触发 Playwright session refresh（日志可见 "Triggering proactive session refresh"）
- [ ] 连续 3 次 poll cycle 失败 → 发送 Telegram 告警，之后 failure 计数归零
- [ ] 任意一次 cycle 成功 → failure 计数归零
- [ ] `TELEGRAM_BOT_TOKEN` 未配置时 → 仅打印 warning，不报错
- [ ] `HEALTH_ALERT_THRESHOLD` 可通过 `.env` 调整

---

## 涉及文件

### 代码
- `src/health.py` — 新建：`FailureTracker` 类 + `send_telegram_alert()`
- `src/scheduler.py` — 修改：接入 FailureTracker，失败时触发 refresh 和告警
- `src/config.py` — 新增：`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `HEALTH_ALERT_THRESHOLD`
- `.env.example` — 新增：Telegram 配置示例

### 文档
- `docs/features/session-health/overview.md`
- `docs/features/session-health/test-guide.md`

---

## 设计决策

- **失败粒度**：以 poll cycle 为单位（不是单个账号）。原因：session 失效会导致所有账号同时失败，cycle 级别更能反映 session 健康状态。
- **首次失败即 refresh**：不等 3 次再 refresh，尽量快速自愈。
- **告警后归零**：避免重复刷屏，每 3 个连续失败 cycle 告警一次。
- **Telegram 可选**：未配置时静默降级，不影响核心采集逻辑。

---

## 验收记录

2026-02-26：实现完成。FailureTracker 逻辑经单元逻辑验证，scheduler 集成完成。
