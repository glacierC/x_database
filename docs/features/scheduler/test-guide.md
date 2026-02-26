# Scheduler — 测试指南

Last Updated: 2026-02-26

---

## 验证防重叠机制

### 方法一：正常运行观察

1. 启动服务：`python main.py`
2. 等待至少两个 cycle 完成（默认 60 分钟 × 2）
3. 在日志中确认：
   - 每个 `=== Poll cycle start ===` 前一定有对应的 `=== Poll cycle done ===`
   - 没有两个 `Poll cycle start` 连续出现而中间没有 `done`

### 方法二：模拟慢 cycle（推荐快速验证）

1. 临时将 `POLL_INTERVAL_MINUTES` 改为 `1`（`.env` 文件）
2. 临时在 `fetch_account()` 中加入 `await asyncio.sleep(90)`，让每次抓取耗时 90 秒
3. 启动服务，观察日志：
   - 1 分钟后第一个 trigger 到达 → 正常启动
   - 再过 1 分钟第二个 trigger 到达 → **不应出现第二个 `Poll cycle start`**
   - 第一个 cycle 结束（90 秒后）→ 才允许下一次抓取
4. 验证完成后恢复原代码

---

## 验证 coalesce（积压合并）

1. 暂停服务（`Ctrl+C`）
2. 等待超过 `POLL_INTERVAL_MINUTES` 的时间（如 2 个间隔）
3. 重启服务
4. 观察日志：恢复后只触发一次 `Poll cycle start`，而不是补跑多次

---

## 日志期望输出

正常情况：
```
INFO  === Poll cycle start ===
INFO  @handle1: N new tweets saved
INFO  @handle2: N new tweets saved
...
INFO  === Poll cycle done ===
（等待 N 分钟）
INFO  === Poll cycle start ===
...
```

异常情况（如果出现以下内容，说明防重叠失效）：
```
INFO  === Poll cycle start ===   ← cycle 1 开始
INFO  === Poll cycle start ===   ← cycle 2 紧接着开始 ← 不应出现！
```
