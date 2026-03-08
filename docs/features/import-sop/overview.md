Last Updated: 2026-03-08

# Import SOP — x_discovery → x_database 批量导入

## 功能是什么

从 x_discovery 评估结果批量导入账号到 x_database，支持本地预览和 VPS 远程执行。

## 使用场景

x_discovery 跑完一批域（如 crypto）的评估后，将 YES 账号导入 x_database 进入 staging，等待 x_digest 自动评估质量后 promote 到生产 group。

## 标准 SOP

```bash
# Step 1 — Review（本地预览，不写库）
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

## 关键 Flag

| Flag | 作用 |
|------|------|
| `--only-new` | 跳过已在 x_database watched_accounts 的账号 |
| `--verbose` | 显示 eval_reason + 2 条 sample tweets（辅助判断） |
| `--dry-run` | 预览，不写库 |
| `--output-format shell` | 输出 cli.py 命令序列（用于 VPS 执行） |
| `--domain` | 只导入指定 domain（crypto / ai_tech / macro / equities / geopolitics）|
| `--min-quality HIGH` | 只导入 HIGH 质量账号 |
| `--promote` | 直接进生产 group，跳过 staging（谨慎使用）|

## 架构原则

- 默认导入进 **staging group**，由 x_digest 48h 自动 eval 决定 promote/drop
- x_database 只执行导入，不做质量判断（那是 x_digest 的事）
