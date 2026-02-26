# 账号管理 + Groups — 测试指南
# Last Updated: 2026-02-26

## 前置条件

在项目根目录，已激活 venv：
```bash
cd x_database
source .venv/bin/activate
```

---

## 1. 账号管理

```bash
# 添加账号
python cli.py account add karpathy sama

# 查看列表
python cli.py account list
# 应看到：karpathy, sama（last fetched: never）

# 删除账号
python cli.py account remove sama
python cli.py account list
# sama 不再出现
```

---

## 2. Group 管理

```bash
# 创建 group
python cli.py group create ai "AI researchers"
python cli.py group create markets "Market observers"

# 分配账号
python cli.py group assign ai karpathy
python cli.py group assign markets karpathy   # 同一账号可属于多个 group

# 查看
python cli.py group show ai
# 应显示：karpathy

python cli.py group list
# 应显示：ai (1 accounts), markets (1 accounts)

# 取消分配
python cli.py group unassign ai karpathy
python cli.py group show ai
# 应显示：(0 accounts)
```

---

## 3. 查询接口

```bash
python -c "
from src.db import get_tweets_by_group
tweets = get_tweets_by_group('ai', since_hours=720, original_only=True)
print(f'Found {len(tweets)} tweets')
if tweets:
    print(tweets[0]['full_text'][:80])
"
```

若 "ai" 组内账号已被采集，应返回 > 0 条推文。

---

## 4. 级联删除验证

```bash
python cli.py account add testuser
python cli.py group assign ai testuser
python cli.py account remove testuser   # 同时清理 group 关联

python cli.py group show ai
# testuser 不再出现
```
