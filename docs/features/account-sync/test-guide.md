# Account 来源管理 — 测试指南
Last Updated: 2026-02-26

## 测试 1：source 列显示

```bash
python cli.py account add testuser1
python cli.py account list
```

预期输出包含 `[manual    ]`：
```
  testuser1                      [manual    ] last fetched: never
```

## 测试 2：X_LIST_ID 未设置时安静跳过

不设置 `X_LIST_ID`（或留空），启动 main.py：
```bash
python main.py
```

预期：日志中**不出现** `List sync` 相关日志，启动正常。

## 测试 3：sync_from_list 逻辑（不需要真实 API）

在 Python 交互环境中：
```python
from src.db import init_db, sync_from_list, get_watched_accounts, add_watched_account

init_db()
add_watched_account("manual_user")  # source='manual'

# 模拟 list sync 添加两个账号
added, removed = sync_from_list(["list_user1", "list_user2"])
assert added == 2 and removed == 0

accounts = {a["handle"]: a["source"] for a in get_watched_accounts()}
assert accounts["list_user1"] == "list_sync"
assert accounts["manual_user"] == "manual"

# 模拟 list_user2 从 List 移除
added, removed = sync_from_list(["list_user1"])
assert removed == 1

accounts = {a["handle"]: a.get("source") for a in get_watched_accounts()}
assert "list_user2" not in accounts  # 已删除
assert "manual_user" in accounts     # 手动账号保留
print("All assertions passed")
```

## 测试 4：X List 同步（需要真实配置）

前置条件：
- `QUERY_ID_LIST_MEMBERS` 已填写
- `X_LIST_ID` 已设置
- cookies 有效

```bash
python main.py
```

在日志中确认：
```
INFO  Starting x_scraper
INFO  X List sync enabled: list_id=<your_id>
INFO  List sync: fetching members for list_id=<your_id>
INFO  X List <id>: fetched N member handles
INFO  List sync done: +N added, -0 removed
```

然后验证：
```bash
python cli.py account list
# 应看到来自 List 的账号，source 显示 list_sync
```
