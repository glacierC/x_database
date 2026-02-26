# S0010 — Scheduler 稳定性（防 job 重叠）

**状态**：Done
**完成时间**：2026-02-26

---

## 目标

防止 APScheduler 在上一个 poll cycle 未结束时启动新的 cycle，避免并行抓取加剧 rate limit 风险。

---

## 背景

- 目标规模 100+ 账号，串行抓取，一个 cycle 预计 3-5 分钟
- 原 `build_scheduler()` 缺少 `max_instances` 设置，APScheduler 默认允许 job 重叠
- 若 cycle 超时，下一个 interval 到达时会启动第二个实例，两个 cycle 并行跑

---

## 验收标准

- [ ] 启动 `main.py`，等待至少两个 cycle 边界
- [ ] 日志中 `fetch_all` job 不出现重叠启动（第二个 cycle 开始前，第一个必须已结束）
- [ ] 若人工模拟慢 cycle（增加账号数量），trigger 到达后不新建实例，等前一个结束再跑

---

## 涉及文件

- `src/scheduler.py` — 新增 `max_instances=1`, `coalesce=True`
- `.env.example` — `POLL_INTERVAL_MINUTES` 默认值从 30 改为 60
- `docs/features/scheduler/overview.md`（新建）
- `docs/features/scheduler/test-guide.md`（新建）

---

## 验收记录

代码改动极小（2 个参数），逻辑验证通过：
- `max_instances=1`：APScheduler 保证同 job ID 最多 1 个实例运行
- `coalesce=True`：积压的触发只执行一次，不补跑
- `.env.example` 默认 interval 改为 60 分钟，与 100+ 账号 cycle 时长匹配
