Last Updated: 2026-03-08

# Import SOP — 测试指南

## 1. Dry-run 验证

```bash
cd x_database
python import_from_discovery_batch.py \
  --discovery-db ../x_discovery/data/x_discovery_crypto.db \
  --only-new --verbose --dry-run
```

预期输出：
- 显示账号列表（handle、quality、noise%、target group）
- `--verbose` 时每个账号下方显示 eval_reason 和 ▸ sample tweets
- 末尾显示 `dry-run 完成，未写库`

## 2. --only-new 验证

预期：输出 `符合条件：N 个 → 扣除已有 M 个 → 新账号：K 个`，K < N。

## 3. --output-format shell 验证

```bash
python import_from_discovery_batch.py \
  --discovery-db ../x_discovery/data/x_discovery_crypto.db \
  --only-new --output-format shell
```

预期输出格式：
```
python cli.py account add handle1
python cli.py group assign staging handle1
python cli.py account add handle2
python cli.py group assign staging handle2
```

检查：每个 handle 都有 `account add` + `group assign staging` 两行。

## 4. 实际导入验证

```bash
python import_from_discovery_batch.py \
  --discovery-db ../x_discovery/data/x_discovery_crypto.db \
  --only-new
```

预期：`✅ 导入完成 [staging（x_digest 48h 后自动 eval）]`，并显示新增/跳过/分配数量。

验证写库：
```bash
sqlite3 data/tweets.db \
  "SELECT handle FROM account_group_members WHERE group_name='staging' LIMIT 10;"
```

## 5. VPS 导入验证

```bash
python import_from_discovery_batch.py --only-new --output-format shell > /tmp/import.sh
cat /tmp/import.sh  # 检查命令内容
# 确认无误后：
scp /tmp/import.sh vps:/tmp/
ssh vps "docker exec -i x_database bash < /tmp/import.sh"
```

预期：VPS 容器内执行 cli.py 命令，账号进入 staging。
