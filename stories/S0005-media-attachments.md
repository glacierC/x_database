# S0005 — 媒体附件记录

**状态**: Done
**完成时间**: 2026-03-01

---

## 目标

将推文中的图片/视频 URL 存入独立的 `media` 表，供下游项目直接查询。

---

## 验收标准

- [ ] 新建 `media` 表（id, tweet_id, media_type, url, video_url）
- [ ] `_parse_tweet()` 从 `legacy.extended_entities.media[]` 提取媒体列表
- [ ] 视频/GIF 取 bitrate 最高的 mp4 URL 存入 `video_url`
- [ ] 媒体插入与 tweet 插入在同一事务内（`insert_tweets()` 内联处理）
- [ ] 验证：`SELECT t.author_handle, m.media_type, m.url FROM media m JOIN tweets t ON m.tweet_id = t.id LIMIT 10;` 有数据

---

## 涉及文件

- `src/db.py`：`media` 表建表 + `insert_media()` 函数 + `insert_tweets()` 更新
- `src/x_api.py`：`_parse_tweet()` 提取 media_items
- `DATABASE.md`：media 表文档新增

---

## 验收记录

**API 字段路径（已从线上 DB raw_json 验证）：**
- `legacy.extended_entities.media[]`（优先）或 `legacy.entities.media[]`
- 每项：`id_str`, `type`, `media_url_https`
- 视频：`video_info.variants[]` 中 `content_type=video/mp4` 且 bitrate 最高者

实现完成，已通过代码审查。等下一个 poll cycle 抓取含媒体推文后可验证数据填充。
