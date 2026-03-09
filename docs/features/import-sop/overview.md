Last Updated: 2026-03-09

# Import SOP — x_discovery → x_database 批量导入

## 功能是什么

从 x_discovery 评估结果批量导入账号到 x_database，直接进指定生产 group。

## 使用场景

x_discovery 跑完一批评估后，将 YES 账号直接导入目标 group（如 crypto、ai_tech）。

## 标准 SOP

```bash
# Step 1 — 本地操作（直接写本地 DB）
python3 -c "
import sqlite3
db = sqlite3.connect('data/tweets.db')
handles = open('../x_discovery/exports/crypto_yes.txt').read().splitlines()
for h in handles:
    db.execute('INSERT OR IGNORE INTO watched_accounts (handle) VALUES (?)', (h,))
    db.execute('INSERT OR IGNORE INTO account_group_members (group_name, handle) VALUES (?, ?)', ('crypto', h))
db.commit()
print(f'{len(handles)} 账号已导入')
"

# Step 2 — 同步到 VPS
scp data/tweets.db home-mac:~/services/x_database/data/tweets.db

# Step 3 — 验证
ssh home-mac "~/.orbstack/bin/docker compose -f ~/services/x_database/docker-compose.yml exec -T app python cli.py group list"
```

## 设计原则

- 直接导入目标 group，无 staging 缓冲
- x_discovery exports/ 保存原始账号列表（core_yes.txt / crypto_yes.txt / top20_yes.txt）作为备份
- 导入前手动决定导入哪个 group、导入多少个

## 可用 exports

| 文件 | 内容 |
|------|------|
| `x_discovery/exports/top20_yes.txt` | 原批次 Top20% YES（184 个）|
| `x_discovery/exports/core_yes.txt` | 原批次中间40% YES（325 个）|
| `x_discovery/exports/crypto_yes.txt` | Crypto 批次 YES（362 个，Top40 已入库）|
