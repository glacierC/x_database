# Account 来源管理
Last Updated: 2026-02-26

## 功能说明

系统支持两种方式向监控列表添加账号，两种方式写入同一个 `watched_accounts` 表：

| 方式 | 命令 / 配置 | source 值 | 适用场景 |
|------|------------|-----------|---------|
| 手动添加 | `python cli.py account add @handle` | `manual` | 零散单个账号 |
| X List 同步 | 设置 `X_LIST_ID=` | `list_sync` | 批量管理 100+ 账号 |

## X List 同步原理

1. 你在 X 上建一个 List，把要监控的账号加进去
2. 系统启动时和每天 00:05 自动读取 List 成员
3. 新成员 → 自动加入 `watched_accounts`
4. 从 List 移除的成员 → 自动从 DB 删除（历史推文保留）

手动添加的账号（`source='manual'`）不受 List 变化影响，需要用 `cli remove` 手动删除。

## 如何开启 X List 同步

### 第一步：获取 List ID
打开你的 X List 页面，URL 格式为：
```
https://x.com/i/lists/1234567890
```
`1234567890` 就是 List ID。

### 第二步：获取 Query ID
ListMembers API 的 Query ID 是 X 内部参数，需要抓包获取：
1. 在浏览器打开你的 X List 页面
2. 按 F12 打开开发者工具 → Network 选项卡
3. 刷新页面，在搜索框过滤 `ListMembers`
4. 找到对应请求，从 URL 中复制 Query ID（`/graphql/<QueryID>/ListMembers`）
5. 填入 `src/x_api.py` 的 `QUERY_ID_LIST_MEMBERS = "..."`

### 第三步：配置环境变量
在 `.env` 文件中设置：
```
X_LIST_ID=1234567890
```

重启 `main.py` 后生效。

## 查看账号来源

```
python cli.py account list
```

输出示例：
```
  elonmusk                       [manual    ] last fetched: 2026-02-26T10:00:00+00:00
  sama                           [list_sync ] last fetched: 2026-02-26T10:01:00+00:00
```
