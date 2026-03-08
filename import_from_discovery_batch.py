"""
从 x_discovery.db 批量导入 YES 账号到 x_database。

用法：
  python import_from_discovery_batch.py                        # 所有 YES，进 staging
  python import_from_discovery_batch.py --domain crypto        # 只导入 crypto domain
  python import_from_discovery_batch.py --min-quality HIGH     # 只导入 HIGH 质量
  python import_from_discovery_batch.py --promote              # 直接进生产 group（跳过 staging）
  python import_from_discovery_batch.py --dry-run              # 预览，不写库
  python import_from_discovery_batch.py --verbose              # 显示 eval_reason + sample tweets
  python import_from_discovery_batch.py --only-new             # 跳过已在 x_database 的账号
  python import_from_discovery_batch.py --output-format shell  # 输出 cli.py 命令（用于 VPS）
  python import_from_discovery_batch.py --discovery-db /path/to/x_discovery_crypto.db

规则：
  - 默认进 staging group（x_digest 自动 eval 后 promote/drop）
  - 用 --promote 跳过 staging，直接进生产 group（谨慎使用）
  - 已存在账号跳过（不覆盖 source/user_id）
  - eval_topics JSON → x_database group 自动映射
"""

import argparse
import json
import os
import sqlite3

# x_discovery.db 默认路径
DEFAULT_DISCOVERY_DB = os.getenv(
    "X_DISCOVERY_DB_PATH",
    os.path.join(os.path.dirname(__file__), "../x_discovery/data/x_discovery.db"),
)

# x_database 路径
XDB_PATH = os.getenv("DB_PATH", "data/tweets.db")

# eval_topics 关键词 → x_database group 映射
TOPIC_TO_GROUP = {
    "crypto": "crypto",
    "bitcoin": "crypto",
    "btc": "crypto",
    "eth": "crypto",
    "defi": "crypto",
    "nft": "crypto",
    "web3": "crypto",
    "ai": "ai_tech",
    "llm": "ai_tech",
    "ml": "ai_tech",
    "tech": "ai_tech",
    "robotics": "ai_tech",
    "macro": "macro",
    "fed": "macro",
    "inflation": "macro",
    "rates": "macro",
    "bonds": "macro",
    "economy": "macro",
    "equities": "equities",
    "stocks": "equities",
    "earnings": "equities",
    "equity": "equities",
    "geopolitics": "geopolitics",
    "politics": "geopolitics",
    "policy": "geopolitics",
}

# x_discovery domain → x_database group 直接映射（比 topics 更精确）
DOMAIN_TO_GROUP = {
    "crypto": "crypto",
    "ai_tech": "ai_tech",
    "macro": "macro",
    "equities": "equities",
    "geopolitics": "geopolitics",
}

PRODUCTION_GROUPS = set(DOMAIN_TO_GROUP.values())


def _topics_to_groups(eval_topics_json: str | None, domain: str | None) -> list[str]:
    """从 eval_topics JSON 和 domain 推断 x_database group 列表。"""
    groups = set()

    # 优先用 domain 直接映射
    if domain and domain in DOMAIN_TO_GROUP:
        groups.add(DOMAIN_TO_GROUP[domain])

    # 再用 eval_topics 补充
    if eval_topics_json:
        try:
            topics = json.loads(eval_topics_json)
            for t in topics:
                t_lower = t.lower()
                for keyword, group in TOPIC_TO_GROUP.items():
                    if keyword in t_lower:
                        groups.add(group)
        except (json.JSONDecodeError, TypeError):
            pass

    # 兜底：如果还是空，用 domain 做模糊匹配
    if not groups and domain:
        for keyword, group in DOMAIN_TO_GROUP.items():
            if keyword in domain.lower():
                groups.add(group)

    return sorted(groups)


def _noise_ratio_to_int(val: str | None) -> int:
    """把 '20/40'（噪音数/样本数）或 '20%' 或 '20' 转成百分比整数。"""
    if not val:
        return 0
    val = str(val).strip()
    try:
        if "/" in val:
            noise, total = val.split("/", 1)
            total_int = int(total)
            return int(int(noise) * 100 / total_int) if total_int else 0
        return int(val.replace("%", ""))
    except (ValueError, ZeroDivisionError):
        return 0


def _load_existing_handles() -> set[str]:
    """返回 x_database 中已有的账号 handle 集合。"""
    try:
        conn = sqlite3.connect(f"file:{XDB_PATH}?mode=ro", uri=True)
        rows = conn.execute("SELECT handle FROM watched_accounts").fetchall()
        conn.close()
        return {r[0].lower() for r in rows}
    except Exception:
        return set()


def load_discovery_accounts(
    discovery_db: str,
    domain_filter: str | None,
    min_quality: str | None,
    max_noise: int,
) -> list[dict]:
    """从 x_discovery.db 读取符合条件的 YES 账号（含 eval_reason + sample_tweets）。"""
    conn = sqlite3.connect(f"file:{discovery_db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    query = "SELECT * FROM accounts WHERE eval_verdict = 'YES'"
    params: list = []

    if domain_filter:
        query += " AND domain = ?"
        params.append(domain_filter)

    if min_quality:
        if min_quality == "HIGH":
            query += " AND eval_quality = 'HIGH'"
        elif min_quality == "MEDIUM":
            query += " AND eval_quality IN ('HIGH', 'MEDIUM')"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        noise = _noise_ratio_to_int(r["eval_noise_ratio"])
        if noise > max_noise:
            continue
        groups = _topics_to_groups(r["eval_topics"], r["domain"])

        # 解析 sample tweets（JSON array）
        sample_tweets = []
        try:
            sample_tweets = json.loads(r["eval_sample_tweets"] or "[]")[:2]
        except (json.JSONDecodeError, TypeError):
            pass

        results.append({
            "handle": r["handle"].lower(),
            "display_name": r["display_name"],
            "domain": r["domain"],
            "eval_quality": r["eval_quality"],
            "eval_noise_ratio": r["eval_noise_ratio"],
            "eval_reason": r["eval_reason"] or "",
            "eval_sample_tweets": sample_tweets,
            "groups": groups,
        })

    return results


def run(
    discovery_db: str,
    domain_filter: str | None,
    min_quality: str | None,
    max_noise: int,
    promote: bool,
    dry_run: bool,
    verbose: bool,
    only_new: bool,
    output_format: str,
):
    accounts = load_discovery_accounts(discovery_db, domain_filter, min_quality, max_noise)

    if not accounts:
        print("⚠️  没有符合条件的账号")
        return

    # --only-new：过滤掉已在 x_database 的账号
    if only_new:
        existing = _load_existing_handles()
        before = len(accounts)
        accounts = [a for a in accounts if a["handle"] not in existing]
        print(f"📋 符合条件：{before} 个 → 扣除已有 {before - len(accounts)} 个 → 新账号：{len(accounts)} 个")
    else:
        print(f"📋 符合条件账号：{len(accounts)} 个")

    if not accounts:
        print("✅ 无新账号需要导入")
        return

    # --output-format shell：输出 cli.py 命令用于 VPS
    if output_format == "shell":
        for acc in accounts:
            handle = acc["handle"]
            target_groups = acc["groups"] if promote else ["staging"]
            print(f"python cli.py account add {handle}")
            for g in target_groups:
                print(f"python cli.py group assign {g} {handle}")
        return

    # 普通输出（dry-run 或实际导入前预览）
    if dry_run:
        print("─── DRY RUN（不写库）───")

    for acc in accounts:
        target_groups = acc["groups"] if promote else ["staging"]
        noise_pct = _noise_ratio_to_int(acc["eval_noise_ratio"])
        print(
            f"  {acc['handle']:30s}  {acc['eval_quality'] or '-':6s}"
            f"  noise={noise_pct}%  → {target_groups}"
        )
        if verbose:
            if acc["eval_reason"]:
                print(f"    → {acc['eval_reason']}")
            for i, tweet in enumerate(acc["eval_sample_tweets"]):
                snippet = str(tweet).replace("\n", " ")[:120]
                print(f"    ▸ {snippet}")

    if dry_run:
        print(f"\n─── 共 {len(accounts)} 个账号，dry-run 完成，未写库 ───")
        return

    # 写库
    conn = sqlite3.connect(XDB_PATH)

    # 确保 staging group 存在
    conn.execute(
        "INSERT OR IGNORE INTO account_groups (name, description) VALUES ('staging', '新入库账号观察区：x_digest 自动 eval 后 promote/drop')"
    )

    added = skipped = assigned = 0
    for acc in accounts:
        handle = acc["handle"]
        cur = conn.execute(
            "INSERT OR IGNORE INTO watched_accounts (handle, source) VALUES (?, 'x_discovery')",
            (handle,),
        )
        if cur.rowcount:
            added += 1
        else:
            skipped += 1

        target_groups = acc["groups"] if promote else ["staging"]
        for g in target_groups:
            if g in PRODUCTION_GROUPS:
                conn.execute(
                    "INSERT OR IGNORE INTO account_groups (name, description) VALUES (?, '')",
                    (g,),
                )
            conn.execute(
                "INSERT OR IGNORE INTO account_group_members (group_name, handle) VALUES (?, ?)",
                (g, handle),
            )
            assigned += 1

    conn.commit()
    conn.close()

    mode = "生产 group（promote）" if promote else "staging（x_digest 48h 后自动 eval）"
    print(f"\n✅ 导入完成 [{mode}]")
    print(f"   新增账号：{added} 个")
    print(f"   已存在跳过：{skipped} 个")
    print(f"   分配 group 关系：{assigned} 条")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从 x_discovery 批量导入 YES 账号")
    parser.add_argument("--discovery-db", default=DEFAULT_DISCOVERY_DB,
                        help=f"x_discovery.db 路径（默认：{DEFAULT_DISCOVERY_DB}）")
    parser.add_argument("--domain", default=None,
                        choices=["crypto", "ai_tech", "macro", "equities", "geopolitics"],
                        help="只导入指定 domain 的账号")
    parser.add_argument("--min-quality", default=None, choices=["HIGH", "MEDIUM"],
                        help="最低质量门槛（HIGH=只导 HIGH；MEDIUM=导 HIGH+MEDIUM）")
    parser.add_argument("--max-noise", type=int, default=60,
                        help="噪音比例上限，百分比整数（默认 60）")
    parser.add_argument("--promote", action="store_true",
                        help="直接进生产 group（跳过 staging，谨慎使用）")
    parser.add_argument("--dry-run", action="store_true",
                        help="预览账号列表，不写库")
    parser.add_argument("--verbose", action="store_true",
                        help="显示 eval_reason + sample tweets（辅助导入决策）")
    parser.add_argument("--only-new", action="store_true",
                        help="跳过已在 x_database watched_accounts 里的账号")
    parser.add_argument("--output-format", default="table", choices=["table", "shell"],
                        help="输出格式：table=人类可读（默认），shell=cli.py 命令（用于 VPS 导入）")
    args = parser.parse_args()

    run(
        discovery_db=args.discovery_db,
        domain_filter=args.domain,
        min_quality=args.min_quality,
        max_noise=args.max_noise,
        promote=args.promote,
        dry_run=args.dry_run,
        verbose=args.verbose,
        only_new=args.only_new,
        output_format=args.output_format,
    )
