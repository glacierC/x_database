# Session 健康检测 — 测试指南
# Last Updated: 2026-02-26

## 1. 验证 FailureTracker 逻辑

```bash
cd x_database
source .venv/bin/activate

python -c "
from src.health import FailureTracker

t = FailureTracker()
print('初始 count:', t.count)          # 0

t.record_failure()
print('1次失败:', t.count)             # 1
print('should_alert:', t.should_alert())  # False (threshold=3)

t.record_failure()
t.record_failure()
print('3次失败:', t.count)             # 3
print('should_alert:', t.should_alert())  # True

t.reset()
print('reset后:', t.count)             # 0

t.record_failure()
t.record_success()
print('成功后:', t.count)              # 0
"
```

---

## 2. 验证 Telegram 未配置时静默降级

```bash
# 确保 .env 里没有配置 TELEGRAM_BOT_TOKEN
python -c "
import asyncio
from src.health import send_telegram_alert
asyncio.run(send_telegram_alert('test'))
"
# 应看到：WARNING - Telegram not configured — skipping alert
# 不应报错
```

---

## 3. 验证 Telegram 真实发送（需已配置）

```bash
python -c "
import asyncio
from src.health import send_telegram_alert
asyncio.run(send_telegram_alert('🧪 测试告警 — 可忽略'))
"
# 你的 Telegram bot 应收到消息
```

---

## 4. 集成验证（日志观察）

正常运行时，观察 `main.py` 日志：

**成功周期（正常情况）**：
```
=== Poll cycle start ===
@karpathy: 2 new tweets saved
=== Poll cycle done ===
```

**失败触发 refresh（第 1 次失败）**：
```
Error fetching @karpathy: ...
Poll cycle: 1/3 accounts failed (consecutive cycles: 1). Failed: ['karpathy']
Triggering proactive session refresh...
Proactive refresh done.
```

**连续 3 次失败触发告警**：
```
Poll cycle: ... (consecutive cycles: 3)
Telegram alert sent.
```

**恢复成功后**：
```
Poll cycle succeeded — resetting failure counter (was 2).
```
