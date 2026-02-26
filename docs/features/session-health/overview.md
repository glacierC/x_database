# Session 健康检测
# Last Updated: 2026-02-26

## 是什么

自动检测 X session 是否失效，失败时触发 cookie 刷新，连续失败时发 Telegram 通知。

让 scraper 可以无人值守长期跑，不用手动盯日志。

---

## 工作流程

```
每次 poll cycle
     │
     ▼
 所有账号抓取完毕
     │
     ├─── 全部成功 ──► 失败计数归零
     │
     └─── 任意失败
              │
              ├─ 第 1 次连续失败 ──► 自动触发 session refresh（Playwright）
              │
              ├─ 第 2 次连续失败 ──► 继续记录
              │
              └─ 第 3 次连续失败 ──► 发 Telegram 告警 → 计数归零
```

---

## 配置

在 `.env` 中添加：

```
TELEGRAM_BOT_TOKEN=你的bot token
TELEGRAM_CHAT_ID=你的chat id
HEALTH_ALERT_THRESHOLD=3   # 可选，默认 3
```

如何获取 Telegram Bot Token：
1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot`，按提示操作
3. 获得 token（格式：`123456:ABC-DEF...`）
4. 和 bot 发一条消息，然后访问 `https://api.telegram.org/bot<token>/getUpdates` 获取 `chat_id`

**如果不配置 Telegram**，系统只打印 warning，不影响采集。

---

## Telegram 告警格式

```
🚨 x_database alert
連続 3 cycle 抓取失敗
最新失敗帳號: @elonmusk, @karpathy
請檢查 session / cookies 狀態。
```

---

## 相关文件

- `src/health.py` — FailureTracker 类 + send_telegram_alert()
- `src/scheduler.py` — 集成健康检测的 poll cycle 逻辑
