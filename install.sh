#!/usr/bin/env bash
# 去往未来 —— 一键安装 / 卸载
#
#   安装:   sudo bash install.sh
#   卸载:   sudo bash install.sh --uninstall            （保留数据）
#           sudo bash install.sh --uninstall --purge    （连数据一起删）
#   升级:   sudo bash install.sh --upgrade              （保留数据与设置）
#
# 会把程序装到 /opt/future-letter，注册 systemd 服务，开机自启。

set -euo pipefail

APP_DIR=/opt/future-letter
SERVICE=future-letter
UNIT=/etc/systemd/system/${SERVICE}.service
RUN_USER=future
PORT_DEFAULT=9000

# 这些是本项目需要的文件
FILES="app.py store.py feeds.py lunar.py quotes.py sysinfo.py themes.py heatmap.py elapsed.py maintenance.py"

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  !\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m  ✗\033[0m %s\n' "$*" >&2; exit 1; }

need_root() {
  [ "$(id -u)" -eq 0 ] || die "请用 sudo 运行：sudo bash install.sh"
}

has_systemd() {
  command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]
}

check_python() {
  command -v python3 >/dev/null 2>&1 || die "没找到 python3，先装：apt install -y python3"
  local ver
  ver=$(python3 -c 'import sys; print("%d%02d" % sys.version_info[:2])')
  [ "$ver" -ge 309 ] || die "需要 Python 3.9 或更高，当前是 $(python3 -V 2>&1)"
  ok "Python $(python3 -V 2>&1 | cut -d' ' -f2)"
}

# ---------------------------------------------------------------- 卸载

do_uninstall() {
  local purge=0
  for arg in "$@"; do
    [ "$arg" = "--purge" ] && purge=1
  done
  need_root

  say "停止并移除服务"
  if has_systemd; then
    systemctl stop "$SERVICE" 2>/dev/null || true
    systemctl disable "$SERVICE" 2>/dev/null || true
    rm -f "$UNIT"
    rm -f "/etc/sudoers.d/${SERVICE}-autostart"
    systemctl daemon-reload
    ok "systemd 服务已移除（含 sudoers 授权）"
  else
    # 没有 systemd 就按进程找
    pkill -f "$APP_DIR/app.py" 2>/dev/null && ok "已停掉运行中的进程" \
      || warn "没找到运行中的进程"
  fi

  if [ "$purge" -eq 1 ]; then
    say "删除程序和数据（--purge）"
    if [ -f "$APP_DIR/data.db" ]; then
      local backup="/root/future-letter-final-$(date +%Y%m%d-%H%M%S).db"
      python3 - "$APP_DIR/data.db" "$backup" <<'PY' || warn "最后一份备份没成功"
import os, shutil, sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(src)
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
target = sqlite3.connect(dst)
conn.backup(target)
target.close()
conn.close()
print("已把最后一份数据存到", dst)
PY
      ok "删除前留了一份在 $backup"
    fi
    rm -rf "$APP_DIR"
    id -u "$RUN_USER" >/dev/null 2>&1 && userdel "$RUN_USER" 2>/dev/null || true
    ok "程序与数据都已删除"
    warn "如果不想留那份保底备份，可以自己 rm $backup"
  else
    say "保留数据（默认行为）"
    echo "  数据还在： $APP_DIR/data.db"
    echo "  备份还在： $APP_DIR/backups/"
    echo "  想彻底删掉： sudo bash install.sh --uninstall --purge"
  fi

  echo
  echo "卸载完成。"
}

# ---------------------------------------------------------------- 安装 / 升级

do_install() {
  local upgrade=0
  for arg in "$@"; do
    [ "$arg" = "--upgrade" ] && upgrade=1
  done
  need_root
  check_python

  local here
  here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
  say "检查项目文件"
  for f in $FILES; do
    [ -f "$here/$f" ] || die "缺少 $f，请在项目目录里运行这个脚本"
  done
  ok "文件齐全"

  say "创建运行用户 $RUN_USER（低权限，不给登录）"
  if id -u "$RUN_USER" >/dev/null 2>&1; then
    ok "用户已存在"
  else
    useradd --system --no-create-home --shell /usr/sbin/nologin "$RUN_USER"
    ok "已创建"
  fi

  say "安装到 $APP_DIR"
  mkdir -p "$APP_DIR"
  for f in $FILES; do
    cp "$here/$f" "$APP_DIR/$f"
  done
  [ -f "$here/check_backup.py" ] && cp "$here/check_backup.py" "$APP_DIR/"
  [ -f "$here/check_sysinfo.py" ] && cp "$here/check_sysinfo.py" "$APP_DIR/"
  [ -f "$here/install.sh" ] && cp "$here/install.sh" "$APP_DIR/"

  # 首次安装才生成配置；升级时绝不覆盖已有配置
  if [ ! -f "$APP_DIR/config.json" ]; then
    python3 - "$APP_DIR/config.json" "$PORT_DEFAULT" <<'PY'
import json, os, secrets, sys
path, port = sys.argv[1], int(sys.argv[2])
cfg = {"port": port,
       "secret": secrets.token_hex(32)}
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)
os.chmod(path, 0o600)
print(f"  已生成配置（端口 {port}）")
PY
    ok "新配置已生成"
  else
    ok "沿用已有配置（升级不覆盖）"
  fi

  if [ ! -f "$APP_DIR/data.db" ]; then
    python3 - "$APP_DIR" <<'PY'
import sys, os
sys.path.insert(0, sys.argv[1])
import store
store.init()
print("  数据库已初始化")
PY
    ok "数据库已建好"
  else
    ok "沿用已有数据库"
  fi

  chown -R "$RUN_USER:$RUN_USER" "$APP_DIR"
  chmod 644 "$APP_DIR"/*.py 2>/dev/null || true
  chmod 600 "$APP_DIR/config.json"
  ok "权限已设置"

  say "授权网页上的「开机自启」开关"
  # 只给这一条最小权限：能 enable/disable 这个服务，别的什么都不给
  if has_systemd && command -v sudo >/dev/null 2>&1; then
    cat > "/etc/sudoers.d/${SERVICE}-autostart" <<SUDOEOF
$RUN_USER ALL=(root) NOPASSWD: /bin/systemctl enable $SERVICE, /bin/systemctl disable $SERVICE, /usr/bin/systemctl enable $SERVICE, /usr/bin/systemctl disable $SERVICE
SUDOEOF
    chmod 440 "/etc/sudoers.d/${SERVICE}-autostart"
    if visudo -c -f "/etc/sudoers.d/${SERVICE}-autostart" >/dev/null 2>&1; then
      ok "已授权（只允许开关这一个服务）"
    else
      rm -f "/etc/sudoers.d/${SERVICE}-autostart"
      warn "sudoers 规则校验没过，已移除；网页开关会提示用命令行"
    fi
  else
    warn "没有 systemd 或没有 sudo，网页上的自启开关不可用（会用命令行提示）"
  fi

  say "注册服务"
  if has_systemd; then
    local port
    port=$(python3 -c "import json;print(json.load(open('$APP_DIR/config.json'))['port'])")
    cat > "$UNIT" <<UNITEOF
[Unit]
Description=Future Letter (time capsule web app)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
Group=$RUN_USER
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 $APP_DIR/app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
# 注意：这里刻意没有 NoNewPrivileges=yes。
# 网页上的「开机自启」开关需要通过 sudo 调 systemctl，
# 而 NNP 会直接禁止 sudo 提权（"The no new privileges flag is set"）。
# 替代的约束是那条极窄的 sudoers 规则：只允许 enable/disable 这一个服务。
NoNewPrivileges=no
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$APP_DIR
# 只放宽 /etc/systemd/system 的读，写仍然禁止
ReadOnlyPaths=/etc/systemd/system

[Install]
WantedBy=multi-user.target
UNITEOF
    systemctl daemon-reload
    systemctl enable "$SERVICE" >/dev/null 2>&1
    systemctl restart "$SERVICE"
    sleep 3

    if systemctl is-active --quiet "$SERVICE"; then
      ok "服务已启动，并设为开机自启"
    else
      warn "服务没起来，日志："
      journalctl -u "$SERVICE" --no-pager -n 20
      die "启动失败"
    fi
  else
    warn "这台机器没有 systemd（可能是容器、WSL、OpenWrt、Alpine 或 macOS）"
    echo "  已装好文件和权限，但没注册开机自启。"
    echo "  手动启动： sudo setpriv --reuid=$RUN_USER --regid=$RUN_USER \\"
    echo "              --clear-groups python3 $APP_DIR/app.py"
    echo "  或用项目里附带的 docker-compose.yml / 自己的 supervisor 托管。"
    # 尝试后台跑起来，至少能立刻访问
    ( setpriv --reuid="$RUN_USER" --regid="$RUN_USER" --clear-groups \
        python3 "$APP_DIR/app.py" >/dev/null 2>&1 & ) || true
    sleep 2
  fi

  local port2
  port2=$(python3 -c "import json;print(json.load(open('$APP_DIR/config.json'))['port'])")
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port2/login" 2>/dev/null || echo 000)
  [ "$code" = "200" ] && ok "登录页可访问" || warn "登录页返回 $code（可能还在启动）"

  # 第一份备份
  if [ "$upgrade" -eq 0 ]; then
    setpriv --reuid="$RUN_USER" --regid="$RUN_USER" --clear-groups \
      python3 "$APP_DIR/app.py" --backup "$APP_DIR/backups/initial.db" \
      >/dev/null 2>&1 || true
  fi

  local ip
  ip=$(hostname -I 2>/dev/null | awk '{print $1}')
  [ -z "${ip:-}" ] && ip=$(hostname -i 2>/dev/null | awk '{print $1}')
  echo
  echo "================================================"
  echo " 装好了。"
  echo
  echo "   地址:  http://${ip:-<这台机器的IP>}:$port2"
  echo "   密码:  weilai2026      ← 登录后请在「设置」里改掉"
  echo
  if has_systemd; then
    echo "   开机自启: 已开启"
  else
    echo "   开机自启: 没开（这台机器没有 systemd）"
  fi
  echo "   数据位置: $APP_DIR/data.db"
  echo "   看日志:   sudo journalctl -u $SERVICE -f"
  echo "   改密码:   cd $APP_DIR && sudo -u $RUN_USER python3 app.py --set-password 新密码"
  echo "   看状态:   cd $APP_DIR && sudo -u $RUN_USER python3 app.py --status"
  echo "   卸载:     sudo bash $APP_DIR/install.sh --uninstall"
  echo "================================================"
}

# ---------------------------------------------------------------- 入口

case "${1:-install}" in
  --uninstall|uninstall)
    shift
    do_uninstall "$@"
    ;;
  --upgrade|upgrade)
    shift
    do_install --upgrade "$@"
    ;;
  --help|-h|help)
    sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    ;;
  install|"")
    do_install "$@"
    ;;
  *)
    die "不认识的参数：$1（用 --help 看用法）"
    ;;
esac
