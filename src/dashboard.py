import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "./data/tweets.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql, params=()):
    conn = get_db()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="60">
<title>x_database Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #0f1117; color: #e2e8f0; padding: 24px; }
  h1 { font-size: 1.4rem; margin-bottom: 4px; }
  .subtitle { color: #718096; font-size: 0.85rem; margin-bottom: 24px; }
  .stats { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
  .stat-card { background: #1a1f2e; border-radius: 8px; padding: 16px 24px; min-width: 140px; }
  .stat-card .num { font-size: 2rem; font-weight: 700; }
  .stat-card .label { font-size: 0.8rem; color: #718096; margin-top: 4px; }
  .stat-card.alert .num { color: #fc8181; }
  .stat-card.ok .num { color: #68d391; }
  h2 { font-size: 1rem; margin: 24px 0 10px; color: #a0aec0; text-transform: uppercase; letter-spacing: 0.05em; }
  table { width: 100%; border-collapse: collapse; background: #1a1f2e; border-radius: 8px; overflow: hidden; margin-bottom: 24px; }
  th { text-align: left; padding: 10px 14px; font-size: 0.75rem; color: #718096; text-transform: uppercase; border-bottom: 1px solid #2d3748; }
  td { padding: 9px 14px; font-size: 0.875rem; border-bottom: 1px solid #232938; }
  tr:last-child td { border-bottom: none; }
  tr.never td { background: #3d1a1a; }
  tr.stale td { background: #3d2a0a; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
  .badge.NEVER { background: #742a2a; color: #fc8181; }
  .badge.STALE { background: #744210; color: #f6ad55; }
  .badge.OK { color: #68d391; }
  .bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 0.8rem; }
  .bar-label { width: 48px; color: #718096; text-align: right; }
  .bar-wrap { flex: 1; background: #2d3748; border-radius: 3px; height: 18px; overflow: hidden; }
  .bar-fill { height: 100%; background: #4299e1; border-radius: 3px; min-width: 2px; }
  .bar-count { width: 40px; color: #a0aec0; }
</style>
</head>
<body>
<h1>x_database Dashboard</h1>
<p class="subtitle">Updated {{ updated }} &nbsp;·&nbsp; auto-refresh every 60s</p>

<div class="stats">
  <div class="stat-card ok">
    <div class="num">{{ summary.total_accounts }}</div>
    <div class="label">Total Accounts</div>
  </div>
  <div class="stat-card {% if summary.never_fetched %}alert{% else %}ok{% endif %}">
    <div class="num">{{ summary.never_fetched }}</div>
    <div class="label">Never Fetched</div>
  </div>
  <div class="stat-card {% if summary.stale %}alert{% else %}ok{% endif %}">
    <div class="num">{{ summary.stale }}</div>
    <div class="label">Stale (&gt;3h)</div>
  </div>
</div>

<h2>Group Overview</h2>
<table>
  <thead>
    <tr>
      <th>Group</th>
      <th>Accounts</th>
      <th>Tweets (1h)</th>
      <th>Tweets (24h)</th>
      <th>Last Active</th>
    </tr>
  </thead>
  <tbody>
    {% for g in groups %}
    <tr>
      <td>{{ g.group_name }}</td>
      <td>{{ g.accounts }}</td>
      <td>{{ g.tweets_1h }}</td>
      <td>{{ g.tweets_24h }}</td>
      <td>{{ g.last_active or '—' }}</td>
    </tr>
    {% else %}
    <tr><td colspan="5" style="color:#718096;text-align:center">No groups found</td></tr>
    {% endfor %}
  </tbody>
</table>

<h2>Recent Activity (24h by hour)</h2>
<div style="background:#1a1f2e;border-radius:8px;padding:16px;margin-bottom:24px">
  {% if hourly %}
  {% set max_count = hourly | map(attribute='count') | max %}
  {% for h in hourly %}
  <div class="bar-row">
    <span class="bar-label">{{ h.hour }}</span>
    <div class="bar-wrap">
      <div class="bar-fill" style="width:{{ [(h.count / max_count * 100), 2] | max }}%"></div>
    </div>
    <span class="bar-count">{{ h.count }}</span>
  </div>
  {% endfor %}
  {% else %}
  <p style="color:#718096;font-size:0.875rem">No tweets in last 24h</p>
  {% endif %}
</div>

<h2>Account Status</h2>
<table>
  <thead>
    <tr>
      <th>Handle</th>
      <th>Groups</th>
      <th>Last Fetch</th>
      <th>Age (min)</th>
      <th>Tweets (24h)</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    {% for a in accounts %}
    <tr class="{{ a.status | lower }}">
      <td>@{{ a.handle }}</td>
      <td>{{ a.groups or '—' }}</td>
      <td>{{ a.last_fetched_at or '—' }}</td>
      <td>{{ a.age_min if a.age_min is not none else '—' }}</td>
      <td>{{ a.tweets_24h }}</td>
      <td><span class="badge {{ a.status }}">{{ a.status }}</span></td>
    </tr>
    {% else %}
    <tr><td colspan="6" style="color:#718096;text-align:center">No accounts found</td></tr>
    {% endfor %}
  </tbody>
</table>
</body>
</html>"""


SQL_SUMMARY = """
SELECT
  COUNT(*) as total_accounts,
  SUM(CASE WHEN last_fetched_at IS NULL THEN 1 ELSE 0 END) as never_fetched,
  SUM(CASE WHEN last_fetched_at < datetime('now','-3 hours') THEN 1 ELSE 0 END) as stale
FROM watched_accounts
"""

SQL_GROUPS = """
SELECT
  gm.group_name,
  COUNT(DISTINCT gm.handle) as accounts,
  SUM(CASE WHEN t.fetched_at >= datetime('now','-1 hours') THEN 1 ELSE 0 END) as tweets_1h,
  SUM(CASE WHEN t.fetched_at >= datetime('now','-24 hours') THEN 1 ELSE 0 END) as tweets_24h,
  MAX(t.fetched_at) as last_active
FROM account_group_members gm
LEFT JOIN tweets t ON t.author_handle = gm.handle
GROUP BY gm.group_name
ORDER BY gm.group_name
"""

SQL_ACCOUNTS = """
SELECT
  wa.handle,
  wa.last_fetched_at,
  GROUP_CONCAT(DISTINCT gm.group_name) as groups,
  COUNT(t.id) as tweets_24h,
  CASE
    WHEN wa.last_fetched_at IS NULL THEN 'NEVER'
    WHEN wa.last_fetched_at < datetime('now','-3 hours') THEN 'STALE'
    ELSE 'OK'
  END as status,
  CASE
    WHEN wa.last_fetched_at IS NULL THEN NULL
    ELSE CAST((julianday('now') - julianday(wa.last_fetched_at)) * 24 * 60 AS INTEGER)
  END as age_min
FROM watched_accounts wa
LEFT JOIN account_group_members gm ON wa.handle = gm.handle
LEFT JOIN tweets t ON t.author_handle = wa.handle
  AND t.fetched_at >= datetime('now','-24 hours')
GROUP BY wa.handle
ORDER BY
  CASE WHEN wa.last_fetched_at IS NULL THEN 0
       WHEN wa.last_fetched_at < datetime('now','-3 hours') THEN 1
       ELSE 2 END,
  wa.last_fetched_at ASC
"""

SQL_HOURLY = """
SELECT
  strftime('%H:00', fetched_at) as hour,
  COUNT(*) as count
FROM tweets
WHERE fetched_at >= datetime('now','-24 hours')
GROUP BY strftime('%H', fetched_at)
ORDER BY hour
"""


@app.route("/")
def index():
    from flask import render_template_string

    summary_rows = query(SQL_SUMMARY)
    summary = summary_rows[0] if summary_rows else {"total_accounts": 0, "never_fetched": 0, "stale": 0}
    groups = query(SQL_GROUPS)
    accounts = query(SQL_ACCOUNTS)
    hourly = query(SQL_HOURLY)

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = render_template_string(
        TEMPLATE,
        updated=updated,
        summary=summary,
        groups=groups,
        accounts=accounts,
        hourly=hourly,
    )
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
