# x_scraper 项目规范
# Last Updated: 2026-02-26

继承 /Users/david/Documents/Code/CC/CLAUDE.md 全部规范。

## 项目特定约定

### 定位边界
- 本项目**只做数据采集**，不做分析、不做展示
- 分析逻辑放独立项目，通过直接读取 `data/tweets.db` 消费数据

### 代码约定
- 所有 X API 调用走 `src/x_api.py`，不在其他地方直接调 httpx
- DB 操作全部走 `src/db.py`，不在其他地方直接写 SQL
- 配置只从 `.env` 读，入口统一在 `src/config.py`

### 敏感文件（永不进 git）
- `cookies/cookies.json` — X session cookies
- `.env` — 包含账号列表等配置
- `data/` — SQLite DB

### X API 维护注意
- `QUERY_ID_USER_BY_SCREEN_NAME` 和 `QUERY_ID_USER_TWEETS` 是 X 内部 ID，X 会不定期更换
- 如果 API 返回 400/404，第一步就是从浏览器 DevTools 更新这两个值（见 `docs/features/scraper/test-guide.md`）

### Story 命名
- 功能：`S000X-xxx.md`
- Bug：`B000X-xxx.md`
