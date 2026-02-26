# x_scraper 测试指南
# Last Updated: 2026-02-26

## 快速验证

```bash
cd x_scraper

# 1. 确认 cookies 存在
ls cookies/cookies.json

# 2. 跑一次采集
python main.py &
sleep 60 && kill %1

# 3. 验证数据写入
sqlite3 data/tweets.db "SELECT author_handle, count(*) FROM tweets GROUP BY author_handle"
```

预期：每个账号都有 > 0 条记录。

## 验证去重

```bash
# 再跑一次，新增数应为 0（除非 X 上有新推文）
python -c "
import asyncio, logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
from src.scheduler import fetch_all_accounts
asyncio.run(fetch_all_accounts())
"
```

预期日志：`@xxx: 0 new tweets saved`

## 验证增量抓取

手动删除 DB 中最新一条推文，再跑一次，应该补回来：

```bash
sqlite3 data/tweets.db "DELETE FROM tweets WHERE id = (SELECT id FROM tweets ORDER BY id DESC LIMIT 1)"
python -c "
import asyncio
from src.scheduler import fetch_all_accounts
asyncio.run(fetch_all_accounts())
"
sqlite3 data/tweets.db "SELECT count(*) FROM tweets"
```

## 常见问题

**采集到 0 条 / RuntimeError: Session appears invalid**
→ cookies 过期，重新从浏览器导出 cookies.json

**API 返回 400/404**
→ X 更换了 GraphQL queryId，需更新 `src/x_api.py` 中的 `QUERY_ID_USER_BY_SCREEN_NAME` 和 `QUERY_ID_USER_TWEETS`（从浏览器 DevTools Network 面板抓取最新值）
