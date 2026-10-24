#!/usr/bin/env bash
# macOS / Linux 上不想装服务，只想跑起来时用这个
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

command -v python3 >/dev/null 2>&1 || {
  echo "没找到 python3。macOS 可以先装： brew install python"
  exit 1
}

echo
echo "  去往未来 正在启动..."
echo "  地址:  http://127.0.0.1:9000"
echo "  密码:  weilai2026      （登录后在「设置」里改）"
echo
echo "  按 Ctrl+C 停掉。"
echo

exec python3 app.py
