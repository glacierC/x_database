# S0014 — 系统治理：Staging 隔离 + 通用批量导入

**状态**：Done（流程暂停）
**完成时间**：2026-03-08
**暂停时间**：2026-03-09

> ⚠️ **2026-03-09 更新**：staging group 已清空并删除。采集上限（~1300 条/小时）下继续扩量性价比低，staging 流程暂停执行。代码保留，如需恢复创建新 story。

---

## 目标

建立 x_discovery → x_database → x_digest 三项目联动的隔离机制与可复用导入流程，防止新账号污染摘要，并替代手写 batchN.py。

---

## 背景

问题：
- x_digest 读取全库所有账号推文（无 group 过滤），任何新账号入库后下一个 cycle 立即进摘要
- 批量导入靠手动硬编码 import_discovery_batch1/2/3.py，无法持续复用

---

## 涉及文件

| 文件 | 改动 |
|------|------|
| `x_database/src/db.py` | init_db 确保 staging group 存在（S0014 P0）|
| `x_digest/src/xdb_reader.py` | get_all_tweets + count_tweets_total 加 production group JOIN 过滤 |
| `x_database/import_from_discovery_batch.py` | 新建通用导入脚本（P1）|

---

## 验收标准

- [ ] staging group 存在于 x_database account_groups 表
- [ ] x_digest 不读取 staging group 账号的推文（xdb_reader.py 有 group JOIN）
- [ ] `python import_from_discovery_batch.py --dry-run` 显示账号列表
- [ ] `python import_from_discovery_batch.py --domain crypto --dry-run` 提示无账号（主 DB），用 `--discovery-db` 指向 x_discovery_crypto.db 后正确显示

---

## 新工作流（S0014 完成后）

```
x_discovery 跑完
  → python import_from_discovery_batch.py [--domain X] [--min-quality HIGH]
  → 账号进 staged（x_digest 看不到）
  → 观察 24-48h 推文质量
  → python cli.py group unassign staging <handle>
  → python cli.py group assign <target_group> <handle>
  → 下次 x_digest cycle 自动包含该账号
```

---

## Promote 质量门控参考

| eval_quality | 建议操作 |
|---|---|
| HIGH | 观察 24h 后可 promote |
| MEDIUM | 观察 48h，人工确认推文风格 |
| LOW | 不导入 |
