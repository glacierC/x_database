"""
x_discovery 第三批 YES 账号导入 — Crypto domain（待 x_discovery 跑完后填入）
用法：python import_discovery_batch3.py

- 新账号写入 watched_accounts（source='x_discovery'），分配到对应 group
- crypto group 首次导入时自动创建
- 已有账号跳过（不覆盖 user_id / source）
"""
import sqlite3, os

DB_PATH = os.getenv("DB_PATH", "data/tweets.db")

# ── 待填入：x_discovery 评估结果（YES 账号列表）────────────────────────────────
# 格式：{"handle": "xxx", "groups": ["crypto", ...]}
# 主要 crypto，也可跨域（如同时属于 macro/equities）
NEW_ACCOUNTS = [
    # TODO: 从 x_discovery batch3 结果粘贴
]

conn = sqlite3.connect(DB_PATH)

# 确保 crypto group 存在
conn.execute(
    "INSERT OR IGNORE INTO account_groups (name, description) VALUES (?, ?)",
    ("crypto", "加密货币：BTC/ETH/链上数据、DeFi、CEX/DEX、监管动态"),
)
conn.commit()

added = skipped = assigned = 0
for acc in NEW_ACCOUNTS:
    h = acc["handle"].lower()
    cur = conn.execute(
        'INSERT OR IGNORE INTO watched_accounts (handle, source) VALUES (?, "x_discovery")',
        (h,),
    )
    if cur.rowcount:
        added += 1
    else:
        skipped += 1
    for g in acc["groups"]:
        conn.execute(
            "INSERT OR IGNORE INTO account_group_members (group_name, handle) VALUES (?, ?)",
            (g, h),
        )
        assigned += 1

conn.commit()
conn.close()
print(f"✅ 新增 {added} 个，跳过 {skipped} 个，{assigned} 条 group 关系")
