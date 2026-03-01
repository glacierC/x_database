# 每日导出 — 测试指南
Last Updated: 2026-03-01

## 手动验证步骤

在项目根目录执行：

```python
from src.exporter import export_all_groups
import os, json

result = export_all_groups(since_hours=24)
print("Exported:", result)

for group, path in result.items():
    assert os.path.exists(path), f"File not found: {path}"
    data = json.load(open(path, encoding="utf-8"))
    assert isinstance(data, list)
    if data:
        assert "author_handle" in data[0]
        assert isinstance(data[0]["media_urls"], list)
    print(f"  {group}: {len(data)} tweets → {path}")

print("All assertions passed ✓")
```

## 预期结果

- 每个 group 生成一个 JSON 文件到 `data/exports/YYYY-MM-DD/<group>.json`
- 每条记录包含 `author_handle`、`full_text`、`media_urls`（列表类型）
- 无 group 或无数据时返回空 `{}` 或空列表，不报错

## Scheduler 验证

检查日志中是否在 06:00 有如下输出：

```
INFO Daily export done: N groups exported. {group_name: file_path, ...}
```

如果某 group 导出失败，日志会有 `ERROR Failed to export group '...'`，但不影响其他 group 继续执行。
