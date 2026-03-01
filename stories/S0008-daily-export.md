# S0008 — 每日导出
Last Updated: 2026-03-01

## 目标
新建 `src/exporter.py`，实现按 group 导出推文为 JSON 文件，并在 scheduler 注册每日 06:00 执行的 cron job。

## 状态：Done
完成时间：2026-03-01

## 验收标准
- [x] `export_group_to_json(group_name, since_hours, original_only)` 返回 list[dict]，含 `media_urls: list`
- [x] `export_all_groups(since_hours, output_dir)` 写入 `{output_dir}/YYYY-MM-DD/<group>.json`，返回路径 map
- [x] scheduler 注册 `daily_export` job，每日 06:00 执行，`max_instances=1` + `coalesce=True`
- [x] 单个 group 导出失败仅记录日志，不中断其他 group

## 涉及文件
- `src/exporter.py`（新建）
- `src/scheduler.py`（修改）
- `docs/features/daily-export/overview.md`（新建）
- `docs/features/daily-export/test-guide.md`（新建）

## 验收记录
`export_group_to_json` 使用 LEFT JOIN + GROUP_CONCAT 一条 SQL 完成，Python 侧将 media_urls 字符串转 list（空时为 []）。
