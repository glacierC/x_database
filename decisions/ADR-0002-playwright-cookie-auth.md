# ADR-0002 - 用 Playwright cookie 维护 X session，httpx 直调 GraphQL

## 背景
需要访问 X 的内部 GraphQL API（非公开 API），必须有有效的登录 session。

## 决策
- 第一次手动登录 X，用 Cookie-Editor 导出 `cookies.json`
- 每次启动从文件直接读取 `auth_token` 和 `ct0`，用 httpx 直接调 GraphQL API
- 只有 token 无效时才启动 Playwright headless 重新加载 cookies 刷新 session

## 原因
- 不需要保持常驻浏览器进程（节省内存，适合 server 环境）
- httpx 异步调用比 Playwright 快很多
- Playwright 只作为 session 刷新工具，不参与每次请求

## 代价
- cookies 有效期约 1 年，但遇到 X 安全检查可能提前失效
- 需要人工导出 cookies（无法全自动化登录，X 有 bot 检测）
- queryId 可能随 X 前端更新而变化，需手动维护

## 日期
2026-02-26
