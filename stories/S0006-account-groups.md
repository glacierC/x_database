# S0006 — 账号管理 + Groups 功能
# Last Updated: 2026-02-26

## 状态：Done
## 完成时间：2026-02-26

---

## 目标

提供命令行工具管理 watched accounts，并新增 Group 机制，让下游项目可以按分组查询推文。

---

## 验收标准

- [ ] `python cli.py account add karpathy` → 成功添加（不报错）
- [ ] `python cli.py account list` → 显示所有账号及最后抓取时间
- [ ] `python cli.py group create ai "AI researchers"` → 创建 group
- [ ] `python cli.py group assign ai karpathy sama` → 两个账号加入 ai 组
- [ ] `python cli.py group show ai` → 显示 karpathy, sama
- [ ] `python cli.py group list` → 显示所有 group 及成员数
- [ ] Python 查询：`get_tweets_by_group("ai", since_hours=720, original_only=True)` → 返回推文列表

---

## 涉及文件

### 代码
- `src/db.py` — 新增 account_groups / account_group_members 表 + 6 个 CRUD 函数
- `cli.py` — 新建，账号和 group 管理命令行工具

### 文档
- `docs/features/account-groups/overview.md`
- `docs/features/account-groups/test-guide.md`

---

## 验收记录

2026-02-26：实现完成，所有 CLI 命令可用，`get_tweets_by_group` 接口可供下游消费。
