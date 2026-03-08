# S0015 — x_discovery → x_database 规范化导入流程

**状态**：Done
**完成时间**：2026-03-08

---

## 目标

建立可重复的 x_discovery → x_database 账号导入 SOP，包括 VPS 导入路径和 x_digest 驱动的自动 promote/drop 机制。

---

## 架构原则

- **x_database = 纯数据层**：只 scrape，不做 promote/drop 决策
- **x_digest = 决策层**：评估 staging 账号内容质量，决定 promote 到哪个 group 或 drop
- **Promote 标准**：x_digest Gemini 对 staging 账号推文的内容质量评估，非推文数量

---

## 涉及文件

| 文件 | 改动 |
|------|------|
| `x_database/import_from_discovery_batch.py` | 新增 `--verbose`、`--only-new`、`--output-format shell` |
| `x_digest/src/xdb_reader.py` | 新增 `get_staging_tweets()` |
| `x_digest/src/staging_eval.py` | 新建：per-account Gemini eval + 写回 x_database + TG 通知 |
| `x_digest/src/scheduler.py` | 新增 48h staging_eval job |
| `x_digest/docker-compose.yml` | x_database volume 从 `:ro` 改为 `:rw`（staging_eval 需要写回） |

---

## 标准导入 SOP

```bash
# Step 1 — Review（本地，看 eval_reason + sample tweets）
python import_from_discovery_batch.py \
  --discovery-db ../x_discovery/data/x_discovery_crypto.db \
  --only-new --verbose --dry-run

# Step 2 — 生成 VPS 导入脚本
python import_from_discovery_batch.py \
  --discovery-db ../x_discovery/data/x_discovery_crypto.db \
  --only-new --output-format shell > /tmp/import.sh

# Step 3 — 推到 VPS 执行
scp /tmp/import.sh vps:/tmp/
ssh vps "docker exec -i x_database bash < /tmp/import.sh"

# Step 4 — 等 48h，x_digest staging_eval 自动运行
# Step 5 — 收 TG 通知：promoted / dropped / observing
```

---

## 验收标准

- [x] `--verbose --dry-run` 显示 eval_reason + sample tweets
- [x] `--only-new` 过滤已有账号（46 个新 vs 203 个已有）
- [x] `--output-format shell` 输出合法 cli.py 命令
- [x] staging_eval 每 48h 自动运行，处理 staging 账号
- [x] x_digest 写回 x_database（promote/drop），发 TG 通知
