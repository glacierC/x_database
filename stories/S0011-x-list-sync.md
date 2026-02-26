# S0011 — Account 来源管理（X List 同步）
# Status: Done
# Completed: 2026-02-26

## 目标
让用户可以在 X 上维护一个 List，系统自动同步 List 成员到 `watched_accounts` 表，
与现有手动 `cli add` 方式并存。

## 验收标准
- [ ] 设置 `X_LIST_ID=<数字ID>` 后，`main.py` 启动时自动同步 List 成员
- [ ] 从 List 移除的账号在下次 sync 后从 DB 删除（仅限 `source='list_sync'`）
- [ ] 手动 `cli add` 的账号 (`source='manual'`) 不受 List 变化影响
- [ ] `python cli.py account list` 输出中显示 `source` 列
- [ ] `X_LIST_ID` 留空时，所有 list sync 代码安静跳过，无副作用

## 涉及文件
- `src/db.py`：`source` 列 migration + `sync_from_list()`
- `src/x_api.py`：`QUERY_ID_LIST_MEMBERS` + `get_list_members()`
- `src/config.py`：`X_LIST_ID`
- `src/scheduler.py`：`sync_watched_list()` + daily cron 00:05
- `main.py`：启动时调用 `sync_watched_list()`
- `cli.py`：`account list` 显示 source
- `.env.example`：新增 `X_LIST_ID=`

## 关键配置步骤
1. 在 x.com 建一个 List，把要监控的账号加进去
2. 打开 List 页面，URL 中取出数字 ID（`x.com/i/lists/<ID>`）
3. 在 x.com 打开 F12 → Network → 过滤 `ListMembers`，记下 query ID
4. 在 `src/x_api.py` 的 `QUERY_ID_LIST_MEMBERS` 填入 query ID
5. 在 `.env` 设置 `X_LIST_ID=<数字ID>`
6. 重启 `main.py`，观察日志 "List sync done"

## 设计决策
- `source` 字段：`'manual'`（cli add）或 `'list_sync'`（X List 同步）
- 删除行为：从 List 移除 → DB 账号删除，历史推文保留（tweets 表不动）
- 同步时机：启动时 + 每日 00:05

## 验收记录
- 实现完成：2026-02-26
- 注：QUERY_ID_LIST_MEMBERS 需用户自行抓包填写后才能实际触发 API 调用
