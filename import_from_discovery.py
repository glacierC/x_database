"""
从 x_discovery 导入 YES 账号到 watched_accounts。
用法：python import_from_discovery.py

- 新账号：写入 watched_accounts（source='x_discovery'），并分配到对应 group
- 已有账号：跳过（不覆盖现有 source/user_id）
- Groups：ai_tech / macro / equities / geopolitics（按 Gemini 评估的 topics 自动映射）
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from src.db import get_conn, init_db

# ── YES 账号数据（由 x_discovery 导出）────────────────────────────────────────
YES_ACCOUNTS = [
  {"handle": "secscottbessent", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "steipete", "groups": ["ai_tech"]},
  {"handle": "alexandr_wang", "groups": ["ai_tech"]},
  {"handle": "garrytan", "groups": ["macro", "ai_tech"]},
  {"handle": "biancoresearch", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "_akhaliq", "groups": ["ai_tech"]},
  {"handle": "friedberg", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "dimartinobooth", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "patrick_oshag", "groups": ["equities", "ai_tech"]},
  {"handle": "sriramk", "groups": ["geopolitics", "ai_tech"]},
  {"handle": "typesfast", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "soumithchintala", "groups": ["ai_tech"]},
  {"handle": "darioamodei", "groups": ["geopolitics", "ai_tech"]},
  {"handle": "oriolvinyalsml", "groups": ["ai_tech"]},
  {"handle": "altcap", "groups": ["macro", "equities", "ai_tech"]},
  {"handle": "lulumeservey", "groups": ["geopolitics", "ai_tech"]},
  {"handle": "percyliang", "groups": ["ai_tech"]},
  {"handle": "eurekalabsai", "groups": ["ai_tech"]},
  {"handle": "ykilcher", "groups": ["ai_tech"]},
  {"handle": "fejau_inc", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "aleks_madry", "groups": ["ai_tech"]},
  {"handle": "gestaltu", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "natesilver538", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "levie", "groups": ["ai_tech"]},
  {"handle": "rishisunak", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "bw", "groups": ["equities", "geopolitics", "macro", "ai_tech"]},
  {"handle": "pmarca", "groups": ["equities", "ai_tech"]},
  {"handle": "kobeissiletter", "groups": ["macro", "equities", "geopolitics"]},
  {"handle": "id_aa_carmack", "groups": ["ai_tech"]},
  {"handle": "wsjmarkets", "groups": ["macro", "equities", "geopolitics"]},
  {"handle": "wsjecon", "groups": ["macro", "geopolitics"]},
  {"handle": "deepseek_ai", "groups": ["ai_tech"]},
  {"handle": "ftchina", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "lynaldencontact", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "peterlbrandt", "groups": ["macro", "equities"]},
  {"handle": "levelsio", "groups": ["macro", "ai_tech"]},
  {"handle": "aiatmeta", "groups": ["equities", "ai_tech"]},
  {"handle": "huggingface", "groups": ["ai_tech"]},
  {"handle": "palmerluckey", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "fchollet", "groups": ["ai_tech"]},
  {"handle": "theallinpod", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "lisaabramowicz1", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "jeffdean", "groups": ["ai_tech"]},
  {"handle": "rabois", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "rasbt", "groups": ["ai_tech"]},
  {"handle": "alphatrends", "groups": ["macro", "equities"]},
  {"handle": "lhsummers", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "awilkinson", "groups": ["equities", "ai_tech"]},
  {"handle": "dacemoglumit", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "harrystebbings", "groups": ["macro", "equities", "ai_tech"]},
  {"handle": "paoloardoino", "groups": ["macro", "equities", "ai_tech"]},
  {"handle": "emollick", "groups": ["ai_tech"]},
  {"handle": "mert", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "saranormous", "groups": ["equities", "ai_tech"]},
  {"handle": "giffmana", "groups": ["ai_tech"]},
  {"handle": "unitreerobotics", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "joshyoung", "groups": ["macro", "equities", "geopolitics"]},
  {"handle": "ericjang11", "groups": ["ai_tech"]},
  {"handle": "thinkymachines", "groups": ["ai_tech"]},
  {"handle": "yimatweets", "groups": ["ai_tech"]},
  {"handle": "dylan522p", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "trengriffin", "groups": ["equities", "ai_tech"]},
  {"handle": "polynoamial", "groups": ["ai_tech"]},
  {"handle": "davidsholz", "groups": ["geopolitics", "ai_tech"]},
  {"handle": "michael_j_black", "groups": ["geopolitics", "ai_tech"]},
  {"handle": "leopoldasch", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "iscienceluvr", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "annaeconomist", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "onechancefreedm", "groups": ["macro", "equities", "geopolitics"]},
  {"handle": "rihardjarc", "groups": ["equities", "ai_tech"]},
  {"handle": "polinaivanovva", "groups": ["macro", "geopolitics"]},
  {"handle": "mansourtarek_", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "gabriel1", "groups": ["macro", "ai_tech"]},
  {"handle": "dee_bosa", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "sirbayes", "groups": ["macro", "ai_tech"]},
  {"handle": "jimmybajimmyba", "groups": ["ai_tech"]},
  {"handle": "luanalopeslara", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "ssankar", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "renmacllc", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "markoinny", "groups": ["macro", "equities", "geopolitics"]},
  {"handle": "bloomberglive", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "willdepue", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "jordanschneider", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "shengjia_zhao", "groups": ["geopolitics", "ai_tech"]},
  {"handle": "connorjbates_", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "binarybits", "groups": ["geopolitics", "ai_tech"]},
  {"handle": "alexwg", "groups": ["macro", "equities", "ai_tech"]},
  {"handle": "jimkxa", "groups": ["ai_tech"]},
  {"handle": "billpeeb", "groups": ["equities", "ai_tech"]},
  {"handle": "eglyman", "groups": ["equities", "ai_tech"]},
  {"handle": "ernietedeschi", "groups": ["macro", "ai_tech"]},
  {"handle": "dan_jeffries1", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "openai", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "sama", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "satyanadella", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "naval", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
  {"handle": "takaichi_sanae", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "nvidia", "groups": ["equities", "ai_tech"]},
  {"handle": "paulg", "groups": ["macro", "equities", "ai_tech"]},
  {"handle": "cathiedwood", "groups": ["macro", "equities", "ai_tech"]},
  {"handle": "markets", "groups": ["macro", "equities", "ai_tech"]},
  {"handle": "anthropicai", "groups": ["geopolitics", "ai_tech"]},
  {"handle": "a16z", "groups": ["equities", "geopolitics", "ai_tech"]},
  {"handle": "gdb", "groups": ["ai_tech"]},
  {"handle": "neal_katyal", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "goldman", "groups": ["ai_tech"]},
  {"handle": "lagarde", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "ecb", "groups": ["macro", "geopolitics"]},
  {"handle": "charliebilello", "groups": ["macro", "equities"]},
  {"handle": "doge", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "business", "groups": ["macro", "equities", "ai_tech"]},
  {"handle": "marketwatch", "groups": ["macro", "equities"]},
  {"handle": "reutersbiz", "groups": ["macro", "equities"]},
  {"handle": "natesilver538", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "rishisunak", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "bw", "groups": ["equities", "geopolitics", "macro", "ai_tech"]},
  {"handle": "wsjecon", "groups": ["macro", "geopolitics"]},
  {"handle": "wsjmarkets", "groups": ["macro", "equities", "geopolitics"]},
  {"handle": "jordanschneider", "groups": ["macro", "geopolitics", "ai_tech"]},
  {"handle": "bloomberglive", "groups": ["macro", "equities", "geopolitics", "ai_tech"]},
]

# 去重
seen = {}
for a in YES_ACCOUNTS:
    seen[a["handle"]] = a
YES_ACCOUNTS = list(seen.values())

GROUP_DESCRIPTIONS = {
    "ai_tech": "AI模型、LLM发展、科技产品、科技行业动态",
    "macro": "宏观经济、美联储政策、通胀、GDP、债券、央行",
    "equities": "美股/港股投资、财报、估值、资金流向",
    "geopolitics": "地缘政治（仅影响市场或全球经济时）",
}


def run():
    init_db()
    conn = get_conn()

    # 创建 groups
    for name, desc in GROUP_DESCRIPTIONS.items():
        conn.execute(
            "INSERT OR IGNORE INTO account_groups (name, description) VALUES (?, ?)",
            (name, desc),
        )
    conn.commit()

    added = skipped = assigned = 0
    for acc in YES_ACCOUNTS:
        handle = acc["handle"].lower()
        # 写入 watched_accounts（已有则跳过）
        cur = conn.execute(
            "INSERT OR IGNORE INTO watched_accounts (handle, source) VALUES (?, 'x_discovery')",
            (handle,),
        )
        if cur.rowcount:
            added += 1
        else:
            skipped += 1

        # 分配 groups
        for g in acc.get("groups", []):
            conn.execute(
                "INSERT OR IGNORE INTO account_group_members (group_name, handle) VALUES (?, ?)",
                (g, handle),
            )
            assigned += 1

    conn.commit()
    conn.close()

    print(f"✅ 导入完成")
    print(f"   新增账号：{added} 个")
    print(f"   已存在跳过：{skipped} 个")
    print(f"   分配 group 关系：{assigned} 条")
    print(f"   Groups：{', '.join(GROUP_DESCRIPTIONS.keys())}")


if __name__ == "__main__":
    run()
