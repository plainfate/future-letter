#!/usr/bin/env bash
# 更新到 v5：热力图、已经多久、设置扩充、后台自动维护
set -euo pipefail

APP_DIR=/opt/future-letter
SERVICE=future-letter
FILES="app.py store.py feeds.py lunar.py themes.py quotes.py sysinfo.py heatmap.py elapsed.py maintenance.py"

echo "=== 语法检查 ==="
for m in $FILES; do
  /usr/bin/python3 -c "import ast; ast.parse(open('$APP_DIR/$m',encoding='utf-8').read())"
  echo "  ok  $m"
done

echo "=== 权限 ==="
chown -R future:future "$APP_DIR"
chmod 644 "$APP_DIR"/*.py
chmod 600 "$APP_DIR/config.json" 2>/dev/null || true
rm -rf "$APP_DIR/__pycache__"

echo "=== 重启 ==="
systemctl restart "$SERVICE"
sleep 3
systemctl is-active "$SERVICE"

echo "=== 页面检查 ==="
for p in "" login news letters time notes quotes settings; do
  printf "  /%-9s " "$p"
  curl -s -o /dev/null -w "%{http_code} %{time_total}s %{size_download}b\n" \
    "http://127.0.0.1:9000/$p"
done

echo "=== 后台维护状态 ==="
journalctl -u "$SERVICE" --no-pager -n 6 | tail -6

echo "=== 数据库 ==="
/usr/bin/python3 -c "
import sqlite3
c = sqlite3.connect('$APP_DIR/data.db')
t = sorted(r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"))
print('  表:', ', '.join(t))
for n in ('letters','days','since','notes','news'):
    if n in t:
        print(f'  {n}:', c.execute('SELECT COUNT(*) FROM ' + n).fetchone()[0], '行')
c.close()
"

echo "=== 备份目录 ==="
ls -lh "$APP_DIR/backups/" 2>/dev/null || echo "  （还没有备份，等后台线程跑）"
