#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「去往未来」——写给未来的信，和一点每天想看的东西。

七个页面：概览 / 信 / 资讯 / 倒数 / 手记 / 摘句 / 设置

关于防跨站：不用 Origin 头判断。iOS「添加到主屏幕」和部分安卓 WebView
会发 Origin: null，用 Origin 判断会把正常操作误杀成「拒绝跨站提交」。
改成每个表单带一个会话派生的一次性令牌，任何设备都能用。

只用标准库。
"""

import gzip
import hashlib
import hmac
import html
import json
import os
import socket
import sqlite3
import subprocess
import sys
import threading
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlsplit

import feeds
import heatmap
import elapsed
import lunar
import maintenance
import quotes
import store
import sysinfo
import themes

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE, "config.json")

DEFAULT_CONFIG = {"port": 9000}
DEFAULT_PASSWORD = "weilai2026"
PBKDF2_ROUNDS = 200_000
COOKIE_NAME = "fy_sid"
SESSION_MAX_AGE = 60 * 60 * 24 * 30

NAV = [
    ("home", "/", "概览"),
    ("letters", "/letters", "信"),
    ("news", "/news", "资讯"),
    ("time", "/time", "时间"),
    ("notes", "/notes", "手记"),
    ("quotes", "/quotes", "摘句"),
    ("settings", "/settings", "设置"),
]

VERSION = "0.1"
SERVICE_NAME = "future-letter"
UNIT_PATH = f"/etc/systemd/system/{SERVICE_NAME}.service"
WANTS_PATH = f"/etc/systemd/system/multi-user.target.wants/{SERVICE_NAME}.service"

MOODS = [("", "无"), ("😊", "开心"), ("🙂", "还行"), ("😐", "平淡"),
         ("😔", "低落"), ("😤", "生气"), ("😴", "累"), ("🤔", "在想事")]

# 提示语用固定码，避免把用户输入回显到页面
MESSAGES = {
    "letter_saved": "这封信已经封存。",
    "letter_deleted": "信已删除。",
    "day_saved": "日子已记下。",
    "day_deleted": "已删除。",
    "since_saved": "记下了，从现在开始算。",
    "since_deleted": "已删除。",
    "note_saved": "记住了。",
    "note_deleted": "这一篇已删除。",
    "settings_saved": "设置已保存。",
    "password_changed": "密码已改好，下次用新密码登录。",
    "news_refreshed": "资讯已刷新。",
    "backup_done": "备份完成。",
    "cache_cleared": "缓存已清理。",
    "autostart_on": "开机自启已开启。",
    "autostart_off": "开机自启已关闭。",
    "imported": "导入完成。",
    "bad_token": "页面太旧了，请刷新后重新提交。",
}

FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
    "%3Crect width='32' height='32' rx='7' fill='%23f2efe6'/%3E"
    "%3Cpath d='M8 11h16v12H8z' fill='none' stroke='%231f4a44' stroke-width='2'/%3E"
    "%3Cpath d='M8 11l8 7 8-7' fill='none' stroke='%231f4a44' stroke-width='2'/%3E"
    "%3C/svg%3E"
)

HELP_TEXT = f"""
去往未来 v{VERSION} —— 写给未来的信，和一点每天想看的东西

用法:
  python3 app.py                      启动网站（默认 9000 端口）
  python3 app.py --help               看这份说明

账号:
  python3 app.py --set-password 新密码      改密码（不用旧密码）

数据:
  python3 app.py --backup 目标.db           备份（会先合并 WAL，别直接 cp）
  python3 app.py --status                   看服务、缓存、数据状态
  python3 app.py --clear-cache              清缓存（Python 缓存、旧备份、旧资讯）
  python3 app.py --clear-cache --keep 5     只保留 5 份备份
  python3 app.py --clear-cache --news 100   只保留 100 条资讯

资讯:
  python3 app.py --refresh-news             立刻抓一次

管理（需要 sudo，卸载用 install.sh）:
  sudo systemctl enable {SERVICE_NAME}      开机自启
  sudo systemctl disable {SERVICE_NAME}     取消开机自启
  sudo systemctl restart {SERVICE_NAME}     重启
  sudo systemctl status {SERVICE_NAME}      看状态
  sudo journalctl -u {SERVICE_NAME} -f      看日志
  sudo bash install.sh --uninstall          卸载（保留数据）
  sudo bash install.sh --uninstall --purge  卸载并删除数据

文件位置:
  程序与数据    /opt/future-letter/
  数据库        /opt/future-letter/data.db
  备份          /opt/future-letter/backups/
  服务定义      {UNIT_PATH}
"""


# ---------------------------------------------------------------- 配置

def save_config(cfg):
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG_PATH)


def load_config():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:
            cfg = json.load(f)
    changed = False
    for key, value in DEFAULT_CONFIG.items():
        if key not in cfg:
            cfg[key] = value
            changed = True
    if "secret" not in cfg:
        cfg["secret"] = hashlib.sha256(os.urandom(32)).hexdigest()
        changed = True
    if changed:
        save_config(cfg)
    return cfg


CFG = load_config()
SECRET = CFG["secret"].encode("utf-8")
PORT = int(CFG["port"])
SESSION_TOKEN = hmac.new(SECRET, b"session-v1", hashlib.sha256).hexdigest()
# 表单令牌：和会话绑定，泄露一个站点的令牌也只能在这个站用
FORM_TOKEN = hmac.new(SECRET, b"form-v1", hashlib.sha256).hexdigest()[:32]


# ---------------------------------------------------------------- 密码

def hash_password(password, salt_hex):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PBKDF2_ROUNDS
    ).hex()


def set_password(password):
    salt_hex = os.urandom(16).hex()
    store.set_setting("password_salt", salt_hex)
    store.set_setting("password_hash", hash_password(password, salt_hex))


def check_password(supplied):
    salt = store.get_setting("password_salt")
    expected = store.get_setting("password_hash")
    if not salt or not expected:
        return False
    return hmac.compare_digest(hash_password(supplied, salt), expected)


def migrate_legacy_password():
    if store.get_setting("password_hash"):
        return
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:
            cfg = json.load(f)
        if cfg.get("password_hash") and cfg.get("password_salt"):
            store.set_setting("password_hash", cfg["password_hash"])
            store.set_setting("password_salt", cfg["password_salt"])
            return
    set_password(DEFAULT_PASSWORD)


# ---------------------------------------------------------------- 小工具

def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def site_title():
    return store.get_setting("site_title", "去往未来")


def current_theme():
    key = store.get_setting("theme", themes.DEFAULT_THEME)
    return key if key in themes.THEMES else themes.DEFAULT_THEME


def current_font():
    key = store.get_setting("font", themes.DEFAULT_FONT)
    return key if key in themes.FONTS else themes.DEFAULT_FONT


def bg_motion():
    return store.get_setting("bg_motion", "1") == "1"


def body_classes():
    """拼 body 的类名：主题专属类 + 背景动效。"""
    cls = [themes.body_class(current_theme())]
    if bg_motion():
        cls.append("bg-motion")
    return " ".join(c for c in cls if c)


def css_url():
    theme = current_theme()
    font = current_font()
    body = themes.css_for(theme, font).encode("utf-8")
    digest = hashlib.sha256(body).hexdigest()[:8]
    return f"/static/style.css?t={theme}&f={font}&v={digest}"


def token_field():
    return f'<input type="hidden" name="_tok" value="{FORM_TOKEN}">'


def days_until(unlock_at):
    try:
        return (date.fromisoformat(unlock_at) - date.today()).days
    except ValueError:
        return 0


def human_days(n):
    if n == 0:
        return "就是今天"
    if n < 0:
        return f"{-n} 天前"
    return f"还有 {n} 天"


def bar(percent):
    if percent is None:
        return ""
    width = max(0, min(100, percent))
    return f'<div class="bar"><i style="width:{width:.0f}%"></i></div>'


def notice_html(code):
    text = MESSAGES.get(code or "")
    return f'<p class="ok">{esc(text)}</p>' if text else ""


def layout(content, active, heading=""):
    title = f"{esc(heading)} · {esc(site_title())}" if heading else esc(site_title())
    nav_html = "".join(
        '<a href="{}"{}>{}</a>'.format(
            href, ' class="on"' if key == active else "", label)
        for key, href, label in NAV
    )
    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,'
        'viewport-fit=cover">\n'
        '<meta name="theme-color" content="#f2efe6">\n'
        f"<title>{title}</title>\n"
        f'<link rel="icon" href="{FAVICON}">\n'
        f'<link rel="stylesheet" href="{css_url()}">\n'
        "</head>\n"
        f'<body class="{body_classes()}">\n'
        '<div class="wrap">\n'
        f'<header><h1 class="brand"><a href="/">{esc(site_title())}</a></h1>'
        f'<nav class="main">{nav_html}</nav></header>\n'
        f"<main>{content}</main>\n"
        '<footer>写给未来 · 时间到了才会打开</footer>\n'
        "</div>\n</body>\n</html>"
    )


# ---------------------------------------------------------------- 日期栏（按天缓存）

_dateline_cache = {"day": None, "html": ""}


def dateline():
    today = date.today()
    if _dateline_cache["day"] == today:
        return _dateline_cache["html"]

    info = lunar.describe_today(today)
    fest = "".join(f'<span class="fest">{esc(n)}</span>'
                   for n in info["today_festivals"])
    nxt = lunar.next_festivals(today, 1)
    upcoming = ""
    if nxt:
        delta, _, name = nxt[0]
        when = "就是今天" if delta == 0 else f"还有 {delta} 天"
        upcoming = f'<span>下一个：{esc(name)} {when}</span>'
    result = (
        '<div class="dateline">'
        f'<b>{esc(info["parts"][0])}</b>'
        f'<span>{esc(info["parts"][1])}</span>'
        f'<span>{esc(info["lunar"])}</span>{fest}{upcoming}</div>'
    )
    _dateline_cache["day"] = today
    _dateline_cache["html"] = result
    return result


def countdown_items():
    today = date.today()
    out = []
    for row in store.days_list():
        try:
            target = date.fromisoformat(row["date"])
        except ValueError:
            continue
        if row["repeat_yearly"]:
            try:
                target = target.replace(year=today.year)
            except ValueError:
                target = target.replace(year=today.year, day=28)
            if target < today:
                try:
                    target = target.replace(year=today.year + 1)
                except ValueError:
                    target = target.replace(year=today.year + 1, day=28)
        delta = (target - today).days
        out.append((delta, row["title"], target, delta == 0, row["id"],
                    bool(row["repeat_yearly"])))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


# ---------------------------------------------------------------- 页面：概览

def view_home(msg=""):
    parts = [dateline(), notice_html(msg)]

    today_iso = date.today().isoformat()
    pending = [r for r in store.letters_list() if r["unlock_at"] > today_iso]
    if pending:
        first = pending[0]
        parts.append(
            f'<a class="card" href="/letter?id={first["id"]}">'
            f'<h3>下一封将拆开的信</h3>'
            f'<h2>{esc(first["title"])}</h2>'
            f'<div class="meta">{esc(first["unlock_at"])} · '
            f'{human_days(days_until(first["unlock_at"]))}</div></a>')
    else:
        parts.append('<div class="card"><h3>还没有等着拆的信</h3>'
                     '<div class="meta">写一封，留给以后的自己。</div></div>')

    # 今日摘句（可在设置里关掉）
    if store.get_setting("home_quote", "1") == "1":
        lang = store.get_setting("quote_lang", "all")
        if lang not in ("all", "zh", "en"):
            lang = "all"
        q = quotes.get(0, lang=lang)
        lang_cls = " en" if q["lang"] == "en" else ""
        tag = "EN" if q["lang"] == "en" else "中"
        parts.append(
            f'<div class="quote" style="margin-top:20px">'
            f'<div class="lang-tag">{tag}</div>'
            f'<p class="body{lang_cls}">{esc(q["body"])}</p>'
            f'<div class="author">— {esc(q["author"])}</div>'
            f'<div class="source">{esc(quote_source(q))}</div>'
            f'<a href="/quotes" style="display:inline-block;margin-top:14px;'
            f'color:var(--accent-ink);font-size:12.5px;text-decoration:none">'
            f'再多看几句 →</a></div>')

    # 已经多久（取最久的三个）
    pairs = [p for p in since_items() if p[1]["forward"]][:3]
    if pairs:
        cards = "".join(
            f'<div class="since-card small">'
            f'<div class="t">{esc(row["title"])}</div>'
            f'<div class="big">{esc(info["span"])}</div>'
            f'<div class="d">共 {info["days"]} 天</div></div>'
            for row, info in pairs)
        parts.append('<h2 class="page sub">已经多久</h2>'
                     f'<div class="since-grid">{cards}</div>')

    items = countdown_items()[:4] if store.get_setting("home_days", "1") == "1" else []
    if items:
        cards = "".join(
            f'<div class="count-card{" today" if is_today else ""}">'
            f'<div class="n">{max(delta, 0)}<small>天</small></div>'
            f'<div class="t">{esc(title)}</div>'
            f'<div class="d">{target.strftime("%m-%d")}'
            f'{" · 每年" if yearly else ""}</div></div>'
            for delta, title, target, is_today, _, yearly in items)
        parts.append('<h2 class="page sub">最近的日子</h2>'
                     f'<div class="count-grid">{cards}</div>')

    today_md = date.today().strftime("%m-%d")
    memories = []
    if store.get_setting("home_memories", "1") == "1":
        memories = [r for r in store.notes_recent(500)
                    if r["entry_date"][5:] == today_md and
                    r["entry_date"] != today_iso]
    if memories:
        rows = "".join(
            f'<div class="item"><div class="src">{esc(r["entry_date"])} '
            f'{esc(r["mood"])}</div>'
            f'<div style="margin-top:3px">{esc(r["body"][:150])}</div></div>'
            for r in memories[:4])
        parts.append('<h2 class="page sub">往年这天</h2>'
                     f'<div class="card">{rows}</div>')

    recent = store.notes_recent(2)
    if recent:
        rows = "".join(
            f'<a class="item" href="/notes?d={esc(r["entry_date"])}" '
            f'style="display:block;text-decoration:none;color:inherit">'
            f'<div class="src">{esc(r["entry_date"])} {esc(r["mood"])}</div>'
            f'<div style="margin-top:3px">{esc(r["body"][:110])}</div></a>'
            for r in recent)
        parts.append('<h2 class="page sub">最近的手记</h2>'
                     f'<div class="card">{rows}</div>')

    return layout("".join(parts), "home")


# ---------------------------------------------------------------- 页面：信

def view_letters(msg=""):
    rows = store.letters_list()
    head = notice_html(msg)
    if not rows:
        content = (head + '<p class="empty">还没有信。<br>'
                   '想对未来说点什么的时候，写给以后的自己。</p>'
                   '<p style="text-align:center"><a href="/new" '
                   'style="color:var(--accent-ink)">写一封 →</a></p>')
        return layout(content, "letters")

    today_iso = date.today().isoformat()
    blocks = [head]
    for r in rows:
        if r["unlock_at"] <= today_iso:
            blocks.append(
                f'<a class="card" href="/letter?id={r["id"]}">'
                f'<h2>{esc(r["title"])}</h2>'
                f'<div class="meta">已解锁 · {esc(r["unlock_at"])}</div></a>')
        else:
            blocks.append(
                f'<a class="card locked" href="/letter?id={r["id"]}">'
                f'<h2>{esc(r["title"])}</h2>'
                f'<div class="cd">{esc(r["unlock_at"])} 开启 · '
                f'还有 {days_until(r["unlock_at"])} 天</div></a>')
    return layout("".join(blocks), "letters")


def view_letter(letter_id):
    row = store.letter_get(letter_id)
    if row is None:
        return None
    if row["unlock_at"] > date.today().isoformat():
        left = days_until(row["unlock_at"])
        content = f"""
<div class="sealed">
  <div class="mark">✉</div>
  <h2>{esc(row["title"])}</h2>
  <p class="meta">这封信还没到打开的时候</p>
  <p class="cd">{human_days(left)} · {esc(row["unlock_at"])} 见</p>
</div>
<p class="meta" style="margin-top:20px;text-align:center">
  写于 {esc(row["created_at"])}</p>"""
        return layout(content, "letters", row["title"])

    content = f"""
<p class="meta">{esc(row["unlock_at"])} 解锁 · 写于 {esc(row["created_at"])}</p>
<h2 class="page" style="margin-top:7px;font-size:22.5px;line-height:1.5">
  {esc(row["title"])}</h2>
<hr class="thin">
<article><div class="letter">{esc(row["body"])}</div></article>
<form method="post" action="/delete"
      onsubmit="return confirm('真的要把这封信删掉吗？删了就找不回来了。')">
  {token_field()}
  <input type="hidden" name="id" value="{row["id"]}">
  <button type="submit" class="ghost">删除这封信</button>
</form>"""
    return layout(content, "letters", row["title"])


def view_new(error=""):
    err = f'<p class="err">{esc(error)}</p>' if error else ""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    content = f"""
<h2 class="page">写一封给未来的信</h2>
<p class="lead">到了那天再打开。在那之前，连你自己也读不到正文。</p>
<form method="post" action="/new">
  {token_field()}
  <label for="title">标题</label>
  <input id="title" name="title" maxlength="120" required
         placeholder="比如：三十岁的我，你好">
  <label for="unlock_at">什么时候可以打开</label>
  <input id="unlock_at" name="unlock_at" type="date" required value="{tomorrow}">
  <label for="body">想说的话</label>
  <textarea id="body" name="body" required
    placeholder="现在的你在想什么？希望以后的你知道些什么？"></textarea>
  {err}
  <button type="submit">封存这封信</button>
</form>"""
    return layout(content, "letters")


# ---------------------------------------------------------------- 页面：资讯

def view_news(msg="", error=""):
    rows = store.news_list(40)
    last = store.news_last_fetch()
    head = (f'<h2 class="page">资讯</h2>'
            f'<p class="lead">{len(rows)} 条 · '
            f'{"更新于 " + esc(last) if last else "还没有抓取过"}</p>'
            '<div style="display:flex;gap:9px;flex-wrap:wrap;align-items:center">'
            '<form method="post" action="/news/refresh" style="margin:0">'
            f'{token_field()}'
            '<button type="submit" class="ghost" style="margin-top:0">'
            '刷新</button></form>'
            '<a href="/settings" class="ghost" style="display:inline-flex;'
            'align-items:center;margin-top:0;padding:10px 15px;'
            'border-radius:10px;border:1px solid var(--line);'
            'color:var(--ink-soft);text-decoration:none;font-size:14px">'
            '管理订阅源</a></div>')
    if msg:
        head += notice_html(msg)
    if error:
        head += f'<p class="err">{esc(error)}</p>'
    if not rows:
        return layout(head + '<p class="empty">还没有内容，点「刷新」拉一次。</p>',
                      "news")

    blocks = []
    for r in rows:
        summary = (f'<div class="src" style="margin-top:2px">'
                   f'{esc(r["summary"])}</div>') if r["summary"] else ""
        blocks.append(
            f'<div class="item">'
            f'<a class="title" href="{esc(r["link"])}" target="_blank" '
            f'rel="noopener noreferrer">{esc(r["title"])}</a>'
            f'<div class="src">{esc(r["feed"])}'
            f'{" · " + esc(r["published"]) if r["published"] else ""}</div>'
            f'{summary}</div>')
    return layout(head + "".join(blocks), "news")


# ---------------------------------------------------------------- 页面：时间

def since_items():
    """已经多久 / 还有多久，统一算好按天数排序。"""
    now = datetime.now()
    out = []
    for row in store.since_list():
        try:
            start = date.fromisoformat(row["start_at"])
        except ValueError:
            continue
        info = elapsed.describe(start, now)
        out.append((row, info))
    out.sort(key=lambda pair: -pair[1]["days"] if pair[1]["forward"]
             else pair[1]["days"])
    return out


def view_time(msg="", error=""):
    err = f'<p class="err">{esc(error)}</p>' if error else ""
    now = datetime.now()

    # ---------- 已经多久 ----------
    pairs = since_items()
    if pairs:
        cards = []
        for row, info in pairs:
            if info["forward"]:
                big = info["span"]
                sub = f'共 {info["days"]} 天 · {info["hours"]:,} 小时'
                if info["is_anniversary"]:
                    sub = "整周年 · " + sub
                mile = ""
                if info.get("milestone_left"):
                    mile = (f'<div class="d">下一个 {info["next_milestone"]} '
                            f'天还有 {info["milestone_left"]} 天</div>')
            else:
                big = f'还有 {info["days"]} 天'
                sub = info["span"]
                mile = ""
            cards.append(
                '<div class="since-card">'
                f'<div class="t">{esc(row["title"])}</div>'
                f'<div class="big">{esc(big)}</div>'
                f'<div class="d">{esc(sub)}</div>{mile}'
                f'<div class="d">从 {esc(row["start_at"])} 起</div>'
                f'<form method="post" action="/since/delete" '
                f'onsubmit="return confirm(\'删掉这条？\')" '
                f'style="position:absolute;top:7px;right:8px;margin:0">'
                f'{token_field()}<input type="hidden" name="id" value="{row["id"]}">'
                f'<button type="submit" class="x" title="删除">×</button></form>'
                '</div>')
        since_html = '<div class="since-grid">' + "".join(cards) + "</div>"
    else:
        since_html = ('<p class="empty">还没有记录。<br>'
                      '"戒烟多久了"、"在一起多久了"、"搬来这座城市多久了"，'
                      '都可以放这儿一直数下去。</p>')

    # ---------- 倒数 ----------
    items = countdown_items()
    if items:
        block = []
        for delta, title, target, is_today, did, yearly in items:
            cls = "count-card today" if is_today else "count-card"
            repeat = " · 每年" if yearly else ""
            block.append(
                '<div class="{}">'
                '<div class="n">{}<small>天</small></div>'
                '<div class="t">{}</div><div class="d">{}{}</div>'
                '<form method="post" action="/days/delete" '
                'onsubmit="return confirm(\'删除这个日子？\')">'
                '{}<input type="hidden" name="id" value="{}">'
                '<button type="submit" title="删除">×</button></form></div>'
                .format(cls, max(delta, 0), esc(title),
                        target.strftime("%Y-%m-%d"), repeat,
                        token_field(), did))
        days_html = '<div class="count-grid">' + "".join(block) + "</div>"
    else:
        days_html = ('<p class="empty">还没有记下的日子。<br>'
                     '生日、考试、纪念日，都可以放这儿倒数。</p>')

    today = date.today().isoformat()
    content = f"""
<h2 class="page">时间</h2>
<p class="lead">有些事在倒数，有些事一直在数。</p>
{notice_html(msg)}{err}

<h2 class="page sub">已经多久</h2>
{since_html}
<form method="post" action="/since/add">
  {token_field()}
  <div class="row">
    <div><label for="stitle">是什么事</label>
      <input id="stitle" name="title" required maxlength="60"
             placeholder="比如：搬来这座城市"></div>
    <div><label for="sstart">从哪天开始</label>
      <input id="sstart" name="start_at" type="date" required value="{today}"></div>
  </div>
  <label for="snote">备注（可不填）</label>
  <input id="snote" name="note" maxlength="120" placeholder="想记住的细节">
  <button type="submit">开始记着</button>
</form>

<h2 class="page sub">还在倒数</h2>
{days_html}
<form method="post" action="/days/add">
  {token_field()}
  <div class="row">
    <div><label for="dtitle">是什么日子</label>
      <input id="dtitle" name="title" required maxlength="60"
             placeholder="比如：妈妈生日"></div>
    <div><label for="ddate">日期</label>
      <input id="ddate" name="date" type="date" required value="{today}"></div>
  </div>
  <label style="display:flex;align-items:center;gap:9px;margin-top:14px">
    <input type="checkbox" name="repeat" value="1"> 每年重复（生日、纪念日勾上）
  </label>
  <button type="submit">记下来</button>
</form>"""
    return layout(dateline() + content, "time")


# ---------------------------------------------------------------- 页面：手记

def quote_source(q):
    """中文出处套书名号，英文出处保持原样。"""
    source = q["source"]
    if q["lang"] == "zh" and not source.startswith("《"):
        return f"《{source}》"
    return source


def view_notes(target_date="", msg="", edit_id=0):
    """手记页：一天的可以写很多条，全部列出来。"""
    if not target_date:
        target_date = date.today().isoformat()
    try:
        day = date.fromisoformat(target_date)
    except ValueError:
        day = date.today()
        target_date = day.isoformat()

    entries = store.notes_by_date(target_date)

    editing = None
    if edit_id:
        editing = store.note_get(edit_id)
        if editing and editing["entry_date"] != target_date:
            editing = None

    info = lunar.solar_to_lunar(day)
    lunar_hint = ""
    if info:
        y, m, d, leap = info
        lunar_hint = f' · {lunar.lunar_month_text(m, leap)}{lunar.lunar_day_text(d)}'

    count_hint = f"{len(entries)} 条" if entries else "还没写"

    # 当天已有的条目
    if entries:
        rows = []
        for r in entries:
            rows.append(
                '<div class="note-item">'
                f'<div class="src">{esc(r["created_at"])}'
                f'{" · " + esc(r["mood"]) if r["mood"] else ""}</div>'
                f'<div class="note-body">{esc(r["body"])}</div>'
                f'<div class="note-actions">'
                f'<a href="/notes?d={esc(target_date)}&amp;edit={r["id"]}" '
                f'class="mini">编辑</a>'
                f'<form method="post" action="/notes/delete" style="margin:0">'
                f'{token_field()}<input type="hidden" name="id" value="{r["id"]}">'
                f'<input type="hidden" name="d" value="{esc(target_date)}">'
                f'<button type="submit" class="mini danger" '
                f'onsubmit="return confirm(\'删掉这条？\')">删除</button></form>'
                f'</div></div>')
        list_html = f'<div class="card">{"".join(rows)}</div>'
    else:
        list_html = ('<p class="empty">这天还没写。<br>'
                     '下面随便写几句，想写几条写几条。</p>')

    # 表单：编辑某条 or 新增
    if editing:
        form_head = (f'修改 <span class="meta">{esc(editing["created_at"])}'
                     f' 那条</span>')
        action = "/notes/update"
        hidden = (f'<input type="hidden" name="id" value="{editing["id"]}">'
                  f'<input type="hidden" name="d" value="{esc(target_date)}">')
        current_mood = editing["mood"]
        current_body = editing["body"]
        submit_text = "保存修改"
        cancel = (f'<a href="/notes?d={esc(target_date)}" class="mini" '
                  f'style="margin-left:9px">取消</a>')
    else:
        form_head = "写点什么"
        action = "/notes/save"
        hidden = f'<input type="hidden" name="d" value="{esc(target_date)}">'
        current_mood = ""
        current_body = ""
        submit_text = "存下来"
        cancel = ""

    mood_options = "".join(
        f'<option value="{esc(v)}"{" selected" if v == current_mood else ""}>'
        f'{esc(label)}{" " + v if v else ""}</option>'
        for v, label in MOODS)

    editor = f"""
<h2 class="page">手记</h2>
<p class="lead">一天可以写很多条。写过的日子会在地图上留下颜色。</p>
{heatmap.render(heatmap.build(store.notes_activity()), "/notes?d=")}
<h2 class="page sub">{esc(target_date)}<span class="meta"
  style="font-weight:400;font-size:13px;margin-left:9px">{esc(lunar_hint)}
  · {esc(count_hint)}</span></h2>
{notice_html(msg)}
{list_html}
<form method="post" action="{action}" style="margin-top:20px">
  {token_field()}{hidden}
  <label for="mood">{esc(form_head)}</label>
  <select id="mood" name="mood">{mood_options}</select>
  <textarea id="nbody" name="body" class="tall" style="margin-top:10px"
    placeholder="随手一句也行。过几年回来看，这些字会不一样。">{esc(current_body)}</textarea>
  <button type="submit">{esc(submit_text)}</button>{cancel}
</form>"""

    # 最近写过的日期
    dates = store.notes_dates()[:30]
    if dates:
        chips = "".join(
            f'<a href="/notes?d={esc(d)}" class="date-chip'
            f'{" on" if d == target_date else ""}">{esc(d[5:])}</a>'
            for d in dates)
        editor += ('<h2 class="page sub">写过的日子</h2>'
                   f'<div class="date-chips">{chips}</div>')
    return layout(editor, "notes")

def view_quotes(offset=0, lang="all"):
    q = quotes.get(offset, lang=lang)
    lang_cls = " en" if q["lang"] == "en" else ""
    tag = "EN" if q["lang"] == "en" else "中文"
    lang_name = {"all": "全部", "zh": "中文", "en": "英文"}[lang]

    filters = "".join(
        '<a href="/quotes?lang={}" style="display:inline-block;margin-right:7px;'
        'padding:8px 14px;border-radius:99px;font-size:13px;'
        'text-decoration:none;border:1px solid {};{}">{}</a>'.format(
            key,
            "var(--accent)" if key == lang else "var(--line)",
            "background:var(--accent);color:#fff" if key == lang
            else "color:var(--ink-soft)",
            label)
        for key, label in (("all", "全部"), ("zh", "中文"), ("en", "英文")))

    # 只有「今天这句」才报序号；随机翻的时候说"第 N 句"没有意义
    if offset:
        lead = f'每天换一句。{lang_name}共 {q["total"]} 句。'
    else:
        lead = (f'每天换一句。{lang_name}共 {q["total"]} 句，'
                f'今天是第 {q["index"] + 1} 句。')
    content = f"""
<h2 class="page">摘句</h2>
<p class="lead">{lead}</p>
<div class="quote">
  <div class="lang-tag">{tag}</div>
  <p class="body{lang_cls}">{esc(q["body"])}</p>
  <div class="author">— {esc(q["author"])}</div>
  <div class="source">{esc(quote_source(q))}</div>
</div>
<div style="display:flex;gap:9px;flex-wrap:wrap;align-items:center">
  <a href="/quotes?lang={lang}&amp;n={offset + 1}"
     style="display:inline-flex;align-items:center;min-height:44px;
     padding:0 20px;border-radius:10px;background:var(--accent);color:#fff;
     text-decoration:none;font-size:15px">换一句</a>
  <a href="/quotes?lang={lang}"
     style="display:inline-flex;align-items:center;min-height:44px;
     padding:0 16px;border-radius:10px;border:1px solid var(--line);
     color:var(--ink-soft);text-decoration:none;font-size:14px">回到今天</a>
</div>
<h2 class="page sub">只看</h2>
<div style="margin-top:8px">{filters}</div>
"""
    return layout(content, "quotes")


# ---------------------------------------------------------------- 页面：设置

def view_settings(msg="", error=""):
    title = site_title()
    theme = current_theme()
    feed_list = feeds.load_feeds()
    feed_text = "\n".join(f'{f.get("name", "")} | {f["url"]}' for f in feed_list)

    # 开关类设置
    def flag(key, default="1"):
        return store.get_setting(key, default) == "1"

    auto_news = flag("auto_news")
    auto_backup = flag("auto_backup")
    show_quote = flag("home_quote")
    show_days = flag("home_days")
    show_memories = flag("home_memories")
    quote_lang = store.get_setting("quote_lang", "all")
    news_hours = store.get_setting("news_interval_hours", "6")
    backup_keep = store.get_setting("backup_keep", "7")

    swatch_cards = ""
    for key, name, desc, swatches in themes.theme_list():
        dots = "".join(f'<i style="background:{s}"></i>' for s in swatches)
        checked = " checked" if key == theme else ""
        swatch_cards += (
            f'<label class="theme-pick">'
            f'<input type="radio" name="theme" value="{key}"{checked}>'
            f'<div class="sw">{dots}</div><div class="nm">{esc(name)}</div>'
            f'<div class="ds">{esc(desc)}</div></label>')

    cur_font = current_font()
    font_cards = ""
    for key, name, desc in themes.font_list():
        checked = " checked" if key == cur_font else ""
        font_cards += (
            f'<label class="theme-pick">'
            f'<input type="radio" name="font" value="{key}"{checked}>'
            f'<div class="nm" style="font-family:'
            f'{esc(themes.FONTS[key]["stack"])}">{esc(name)}</div>'
            f'<div class="ds">{esc(desc)}</div>'
            f'<div class="ds" style="margin-top:6px;font-family:'
            f'{esc(themes.FONTS[key]["stack"])}">今天写了 128 个字 · 2026</div>'
            f'</label>')

    def toggle(name, checked, label, hint=""):
        on = " checked" if checked else ""
        hint_html = f'<div class="hint">{esc(hint)}</div>' if hint else ""
        return (f'<label class="switch"><input type="checkbox" name="{name}" '
                f'value="1"{on}><span>{esc(label)}</span></label>{hint_html}')

    msg_html = notice_html(msg) + (f'<p class="err">{esc(error)}</p>' if error else "")

    info = sysinfo.collect(store.DB_PATH)
    counts = store.stats()
    maint = maintenance.state()
    backups = maintenance.list_backups()
    svc = service_state()
    cache = cache_info()

    cli_block = "\n".join([
        "# 开机自启（网页上的开关失败时用这个）",
        CLI_HINTS["autostart_on"],
        CLI_HINTS["autostart_off"],
        "",
        "# 启停与日志",
        CLI_HINTS["restart"],
        CLI_HINTS["status"],
        CLI_HINTS["logs"],
        "",
        "# 清缓存（也可以在设置页点按钮）",
        f"cd /opt/future-letter && {CLI_HINTS['clear_cache']}",
        "",
        "# 卸载（默认保留数据；加 --purge 才连数据一起删）",
        CLI_HINTS["uninstall"],
    ])

    # 自启开关是否可用，取决于装的时候有没有写那条 sudoers 规则
    sudoers_ok = os.path.exists(
        f"/etc/sudoers.d/{SERVICE_NAME}-autostart")
    on = svc["autostart"]
    on_checked = " checked" if on else ""
    off_checked = " checked" if not on else ""
    on = " on" if on else ""
    off = " off" if not svc["autostart"] else ""
    if sudoers_ok:
        autostart_hint = '<div class="hint">改动会直接生效。</div>'
    else:
        autostart_hint = (
            '<div class="hint">这台机器还没授权网页改自启，上面的保存会提示失败。'
            f'用一次 <code>sudo bash /opt/{SERVICE_NAME}/install.sh --upgrade</code> '
            '授权后就能直接点。现在请用下面的命令。</div>')

    def cell(key, value, extra=""):
        return (f'<div class="sys-cell"><div class="k">{esc(key)}</div>'
                f'<div class="v">{value}{extra}</div></div>')

    load = info["load"]
    load_text = (f'{load[0]:.2f} <small>/ {load[1]:.2f} / {load[2]:.2f}</small>'
                 if load else "—")
    mem_text = (f'{info["mem_used"]:.0f} <small>/ {info["mem_total"]:.0f} MB</small>'
                if info["mem_used"] is not None else "—")
    disk_text = (f'{info["disk_used"]:.1f} <small>/ {info["disk_total"]:.1f} GB</small>'
                 if info["disk_used"] is not None else "—")
    temp_text = f'{info["temp"]:.0f} <small>°C</small>' if info["temp"] else "—"
    proc_text = (f'{info["proc_rss"]:.0f} <small>MB</small>'
                 if info["proc_rss"] is not None else "—")
    db_kb = info["db_size_kb"]
    db_text = (f'{db_kb:.0f} <small>KB</small>' if db_kb is not None else "—")

    sys_cells = "".join([
        cell("主机", esc(info["hostname"])),
        cell("系统", esc(info["os"])),
        cell("运行时长", esc(info["uptime"])),
        cell("CPU 核心", f'{info["cpus"]}'),
        cell("负载 1/5/15", load_text),
        cell("CPU 温度", temp_text),
        cell("内存", mem_text, bar(info["mem_percent"])),
        cell("磁盘", disk_text, bar(info["disk_percent"])),
        cell("本程序内存", proc_text),
        cell("数据库", db_text),
    ])
    counts_text = " · ".join(
        f'{name} {counts[k]}' for name, k in
        (("信", "letters"), ("日子", "days"), ("手记", "notes"), ("资讯", "news")))

    backup_rows = ""
    for b in backups[:6]:
        backup_rows += (
            f'<div class="item"><div class="src">{esc(b["mtime"])}</div>'
            f'<div style="margin-top:2px">{esc(b["name"])} · '
            f'{b["size_kb"]:.0f} KB</div></div>')
    backup_list = (f'<div class="card" style="margin-top:10px">{backup_rows}</div>'
                   if backup_rows else
                   '<p class="hint">还没有自动备份。开启后每天会存一份。</p>')

    last_news = maint.get("last_news") or "—"
    last_backup = maint.get("last_backup") or "—"
    errors = maint.get("errors") or []
    error_html = ""
    if errors:
        error_html = ('<p class="hint" style="color:#b5544a">最近的问题：<br>'
                      + "<br>".join(esc(e) for e in errors[-3:]) + "</p>")

    return layout(f"""
<h2 class="page">设置</h2>
{msg_html}

<form method="post" action="/settings/save">
  {token_field()}
  <label for="stitle">站点名字</label>
  <input id="stitle" name="site_title" maxlength="40" value="{esc(title)}">
  <label>配色（点一下选中，保存后整个站生效）</label>
  <div class="themes">{swatch_cards}</div>

  <label>字体</label>
  <div class="themes">{font_cards}</div>
  <div class="hint">「像素」会用上你系统里装的像素字体（Zpix、缝合像素等）；
    没装就退到等宽字体。</div>

  <label>背景</label>
  {toggle("bg_motion", bg_motion(), "让背景轻轻流动",
          "很慢的呼吸式移动，不晃眼。系统开了「减少动效」时会自动停。")}
  <label for="feeds">资讯源（每行一个：名称 | RSS 地址）</label>
  <textarea id="feeds" name="feeds" style="min-height:120px">{esc(feed_text)}</textarea>
  <div class="hint">留空则恢复默认五个源：36氪、少数派、Solidot、IT之家、开源中国。</div>

  <label>首页放什么</label>
  {toggle("home_quote", show_quote, "今日摘句", "概览顶部显示一句")}
  {toggle("home_days", show_days, "临近的日子", "把最接近的四个日子摆出来")}
  {toggle("home_memories", show_memories, "往年这天", "同月同日写过的手记")}

  <label for="quote_lang">摘句默认语言</label>
  <select id="quote_lang" name="quote_lang">
    <option value="all"{" selected" if quote_lang == "all" else ""}>中英都有</option>
    <option value="zh"{" selected" if quote_lang == "zh" else ""}>只要中文</option>
    <option value="en"{" selected" if quote_lang == "en" else ""}>只要英文</option>
  </select>

  <button type="submit">保存设置</button>
</form>

<h2 class="page sub">让机器自己干活</h2>
<p class="lead">这些都在后台跑，不用你管。</p>
<form method="post" action="/settings/auto">
  {token_field()}
  {toggle("auto_news", auto_news, "定时抓资讯",
          "按下面的间隔自动刷新，打开资讯页时就不必等")}
  <label for="news_interval">抓取间隔</label>
  <select id="news_interval" name="news_interval_hours">
    <option value="1"{" selected" if news_hours == "1" else ""}>每 1 小时</option>
    <option value="3"{" selected" if news_hours == "3" else ""}>每 3 小时</option>
    <option value="6"{" selected" if news_hours == "6" else ""}>每 6 小时</option>
    <option value="12"{" selected" if news_hours == "12" else ""}>每 12 小时</option>
    <option value="24"{" selected" if news_hours == "24" else ""}>每天一次</option>
  </select>

  {toggle("auto_backup", auto_backup, "每天自动备份",
          "自动合并 WAL 后存一份，这是你数据的唯一副本，建议开着")}
  <label for="backup_keep">保留几份备份</label>
  <select id="backup_keep" name="backup_keep">
    <option value="3"{" selected" if backup_keep == "3" else ""}>3 份</option>
    <option value="7"{" selected" if backup_keep == "7" else ""}>7 份</option>
    <option value="14"{" selected" if backup_keep == "14" else ""}>14 份</option>
    <option value="30"{" selected" if backup_keep == "30" else ""}>30 份</option>
  </select>

  <div class="hint">上次抓资讯：{esc(last_news)} · 上次备份：{esc(last_backup)}</div>
  {error_html}
  <button type="submit">保存</button>
</form>

<h2 class="page sub">数据</h2>
<div style="display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-top:6px">
  <form method="post" action="/settings/backup" style="margin:0">
    {token_field()}
    <button type="submit" style="margin-top:0">立即备份一次</button>
  </form>
  <a href="/export.json" style="display:inline-flex;align-items:center;
     min-height:44px;padding:0 18px;border-radius:10px;
     border:1px solid var(--line);color:var(--ink-soft);text-decoration:none;
     font-size:15px">导出全部数据（JSON）</a>
</div>
{backup_list}

<label for="import">从 JSON 导入（会追加，不会删掉现有内容）</label>
<form method="post" action="/settings/import">
  <textarea id="import" name="payload" style="min-height:110px"
    placeholder="把之前导出的 JSON 贴在这里"></textarea>
  <div class="hint">信的正文也会一起导入。导入后请自己核对一遍。</div>
  <button type="submit" class="ghost" style="margin-top:12px">导入</button>
</form>

<h2 class="page sub">改密码</h2>
<p class="lead">改完不用重新登录，但要记住新密码。</p>
<form method="post" action="/settings/password">
  {token_field()}
  <label for="oldpw">现在的密码</label>
  <input id="oldpw" name="old" type="password" required
         autocomplete="current-password">
  <label for="newpw">新密码</label>
  <input id="newpw" name="new" type="password" required minlength="6"
         autocomplete="new-password">
  <label for="newpw2">再输一次</label>
  <input id="newpw2" name="confirm" type="password" required minlength="6"
         autocomplete="new-password">
  <button type="submit">改密码</button>
</form>

<h2 class="page sub">这台机器</h2>
<p class="lead">{esc(counts_text)}</p>
<div class="sys-grid">{sys_cells}</div>

<h2 class="page sub">启动与管理</h2>
<p class="lead">开关和端口都能在这儿直接改。卸载要用命令行（需要 root）。</p>
<div class="sys-grid">
  <div class="sys-cell"><div class="k">开机自启</div>
    <div class="v">{'已开启' if svc['autostart'] else '已关闭'}</div></div>
  <div class="sys-cell"><div class="k">服务</div>
    <div class="v">{'运行中' if svc['running'] else '已停止'}</div></div>
  <div class="sys-cell"><div class="k">端口</div>
    <div class="v">{svc['port']}</div></div>
  <div class="sys-cell"><div class="k">缓存占用</div>
    <div class="v">{cache['pycache_kb']:.0f} <small>KB</small></div></div>
  <div class="sys-cell"><div class="k">WAL 文件</div>
    <div class="v">{cache['wal_kb']:.0f} <small>KB</small></div></div>
  <div class="sys-cell"><div class="k">备份占用</div>
    <div class="v">{cache['backup_kb']:.0f} <small>KB</small>
      <small style="display:block">共 {cache['backup_count']} 份</small></div></div>
</div>

<form method="post" action="/settings/autostart" style="margin-top:16px">
  {token_field()}
  <label>开机自启</label>
  <div class="radio-row">
    <label class="radio-pick{on}">
      <input type="radio" name="enable" value="1"{on_checked}> 开启
    </label>
    <label class="radio-pick{off}">
      <input type="radio" name="enable" value="0"{off_checked}> 关闭
    </label>
    <button type="submit" style="margin:0">保存</button>
  </div>
  <div class="hint">当前状态：{'已开启，开机自动运行' if svc['autostart'] else '已关闭，需手动启动'}。</div>
</form>
{autostart_hint}

<form method="post" action="/settings/port" style="margin-top:22px"
      onsubmit="return confirm('改端口后页面会短暂断开，新地址是「当前IP:新端口」。确定要改吗？')">
  {token_field()}
  <label for="newport">端口（改了会立刻重启到新端口）</label>
  <div class="row">
    <div><input id="newport" name="port" type="number" min="1024" max="65535"
                value="{svc['port']}" required></div>
    <div style="flex:0 0 auto">
      <button type="submit" style="margin-top:0">改端口</button>
    </div>
  </div>
  <div class="hint">建议用 1024 以上。改完当前页面可能打不开，换
    <code>http://这里IP:新端口</code> 访问即可。</div>
</form>

<div style="display:flex;gap:9px;flex-wrap:wrap;align-items:center;
     margin-top:16px">
  <form method="post" action="/settings/clearcache" style="margin:0"
        onsubmit="return confirm('清理缓存？只删缓存和旧备份，不动你的信和手记。')">
    {token_field()}
    <button type="submit" style="margin-top:0">清理缓存</button>
  </form>
</div>
<div class="hint">会清掉：Python 缓存、超出保留数的旧备份、资讯里过老的条目，
  并给数据库瘦身。信件、手记、日子一律不动。</div>

<label>命令行能做同样的事（复制即用）</label>
<div class="card" style="padding:12px 15px">
  <pre style="margin:0;overflow-x:auto;font-size:12px;line-height:1.9;
       color:var(--ink-soft);font-family:ui-monospace,Menlo,Consolas,monospace">{cli_block}</pre>
</div>

<h2 class="page sub">关于</h2>
<div class="card">
  <div class="meta">去往未来 v{VERSION} · Python {sys.version.split()[0]} · 零第三方依赖</div>
  <div class="meta">内核 {esc(info["kernel"])} · 监听 {PORT} 端口 · 登录状态保持 30 天</div>
  <div class="meta">所有内容都在 data.db 一个文件里</div>
  <div class="meta" style="margin-top:8px">
    <a href="/logout" style="color:var(--accent-ink)">退出登录</a></div>
</div>
""", "settings")


def view_login(error=""):
    err = f'<p class="err">{esc(error)}</p>' if error else ""
    return layout(f"""
<h2 class="page">先确认是你</h2>
<p class="lead">这里只给你自己看，输一次密码，之后就记着你了。</p>
<form method="post" action="/login">
  <label for="pw">密码</label>
  <input id="pw" name="password" type="password" autofocus required
         autocomplete="current-password">
  {err}
  <button type="submit">进入</button>
</form>""", "")


# ---------------------------------------------------------------- HTTP

class Handler(BaseHTTPRequestHandler):
    server_version = "FutureLetter/4.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - [%s] %s\n" % (
            self.address_string(), self.log_date_time_string(), fmt % args))

    # -- 输出 --

    def _accepts_gzip(self):
        return "gzip" in (self.headers.get("Accept-Encoding") or "")

    def _send(self, code, body, ctype="text/html; charset=utf-8",
              cache="no-cache", extra_headers=None):
        raw = body.encode("utf-8") if isinstance(body, str) else body
        etag = '"' + hashlib.md5(raw).hexdigest()[:16] + '"'

        if cache == "no-cache":
            if (self.headers.get("If-None-Match") or "").strip() == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.send_header("Cache-Control", cache)
                # 304 也要给 Content-Length，否则长连接可能错位
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

        payload = raw
        use_gzip = len(raw) > 500 and self._accepts_gzip()
        if use_gzip:
            payload = gzip.compress(raw, 6)

        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", cache)
        self.send_header("ETag", etag)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        for key, value in (extra_headers or []):
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _redirect(self, location, extra=None):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        for k, v in (extra or []):
            self.send_header(k, v)
        self.end_headers()

    def _body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > 3_000_000:
            return ""
        return self.rfile.read(length).decode("utf-8", "replace")

    def _form(self):
        return {k: v[0] for k, v in
                parse_qs(self._body(), keep_blank_values=True).items()}

    def _query(self):
        return {k: v[0] for k, v in
                parse_qs(urlsplit(self.path).query, keep_blank_values=True).items()}

    def _path(self):
        return urlsplit(self.path).path.rstrip("/") or "/"

    def _authed(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            key, _, value = part.strip().partition("=")
            if key == COOKIE_NAME:
                return hmac.compare_digest(value.strip(), SESSION_TOKEN)
        return False

    def _token_ok(self, form):
        """表单令牌。不依赖 Origin —— WebView 和主屏幕应用会发 Origin: null。"""
        supplied = (form.get("_tok") or "").strip()
        return bool(supplied) and hmac.compare_digest(supplied, FORM_TOKEN)

    # -- GET --

    def do_GET(self):
        path = self._path()
        q = self._query()

        if path == "/static/style.css":
            key = q.get("t", themes.DEFAULT_THEME)
            font = q.get("f", themes.DEFAULT_FONT)
            css = themes.css_for(
                key if key in themes.THEMES else themes.DEFAULT_THEME,
                font if font in themes.FONTS else themes.DEFAULT_FONT)
            self._send(200, css, "text/css; charset=utf-8",
                       cache="public, max-age=31536000, immutable")
            return

        if path == "/login":
            self._send(200, view_login())
            return
        if path == "/logout":
            self._redirect("/login", extra=[(
                "Set-Cookie",
                f"{COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")])
            return
        if not self._authed():
            self._redirect("/login")
            return

        if path == "/":
            self._send(200, view_home(q.get("m", "")))
        elif path == "/letters":
            self._send(200, view_letters(q.get("m", "")))
        elif path == "/new":
            self._send(200, view_new())
        elif path == "/letter":
            try:
                letter_id = int(q.get("id", "0"))
            except ValueError:
                letter_id = 0
            page = view_letter(letter_id)
            if page is None:
                self._send(404, layout('<p class="empty">没有这封信。</p>', "letters"))
            else:
                self._send(200, page)
        elif path == "/news":
            self._maybe_refresh_news()
            self._send(200, view_news(q.get("m", "")))
        elif path in ("/time", "/days"):
            self._send(200, view_time(q.get("m", "")))
        elif path == "/notes":
            try:
                edit_id = int(q.get("edit", "0") or 0)
            except ValueError:
                edit_id = 0
            self._send(200, view_notes(q.get("d", ""), q.get("m", ""), edit_id))
        elif path == "/quotes":
            try:
                offset = int(q.get("n", "0"))
            except ValueError:
                offset = 0
            lang = q.get("lang", store.get_setting("quote_lang", "all"))
            if lang not in ("all", "zh", "en"):
                lang = "all"
            self._send(200, view_quotes(offset, lang))
        elif path == "/settings":
            self._send(200, view_settings(q.get("m", "")))
        elif path == "/export.json":
            payload = export_json()
            self._send(200, payload, "application/json; charset=utf-8",
                       extra_headers=[("Content-Disposition",
                                       'attachment; filename="future-letter.json"')])
        else:
            self._send(404, layout('<p class="empty">这里什么都没有。</p>', ""))

    def do_HEAD(self):
        self.do_GET()

    def _maybe_refresh_news(self):
        last = store.news_last_fetch()
        stale = True
        if last:
            try:
                delta = datetime.now() - datetime.strptime(last, "%Y-%m-%d %H:%M")
                stale = delta.total_seconds() > 1800
            except ValueError:
                stale = True
        if stale and not _refresh_lock.locked():
            threading.Thread(target=_safe_refresh, daemon=True).start()

    # -- POST --

    def do_POST(self):
        path = self._path()

        if path == "/login":
            if check_password(self._form().get("password", "")):
                self._redirect("/", extra=[(
                    "Set-Cookie",
                    f"{COOKIE_NAME}={SESSION_TOKEN}; Path=/; "
                    f"Max-Age={SESSION_MAX_AGE}; HttpOnly; SameSite=Lax")])
            else:
                self._send(401, view_login("密码不对，再试一次。"))
            return

        if not self._authed():
            self._redirect("/login")
            return

        form = self._form()

        # 令牌不对：既不执行，也不泄露任何东西，只提示刷新
        if not self._token_ok(form):
            self._send(400, layout(
                '<div class="card"><h3>页面太旧了</h3>'
                '<div class="meta">这个表单来自旧页面，令牌已经对不上了。'
                '刷新一下再提交就好。</div>'
                '<a href="/" style="display:inline-block;margin-top:12px;'
                'color:var(--accent-ink)">回到首页</a></div>', ""))
            return

        if path == "/new":
            title = (form.get("title") or "").strip()
            body = (form.get("body") or "").strip()
            unlock_at = (form.get("unlock_at") or "").strip()
            error = ""
            if not title:
                error = "信总得有个标题。"
            elif not body:
                error = "正文是空的。"
            else:
                try:
                    date.fromisoformat(unlock_at)
                except ValueError:
                    error = "开启日期格式不对。"
            if error:
                self._send(400, view_new(error))
                return
            store.letter_add(title, body, unlock_at)
            self._redirect("/letters?m=letter_saved")

        elif path == "/delete":
            try:
                store.letter_delete(int(form.get("id", "0")))
            except ValueError:
                pass
            self._redirect("/letters?m=letter_deleted")

        elif path == "/news/refresh":
            ok, failures = feeds.refresh_all()
            if failures and ok == 0:
                self._send(200, view_news(
                    error="这次的源都没取到（" + "；".join(failures[:2]) + "）"))
            else:
                self._redirect("/news?m=news_refreshed")

        elif path == "/days/add":
            title = (form.get("title") or "").strip()
            when = (form.get("date") or "").strip()
            if not title:
                self._send(400, view_time(error="得给这个日子起个名字。"))
                return
            try:
                date.fromisoformat(when)
            except ValueError:
                self._send(400, view_time(error="日期格式不对。"))
                return
            store.day_add(title, when, form.get("repeat") == "1")
            self._redirect("/time?m=day_saved")

        elif path == "/days/delete":
            try:
                store.day_delete(int(form.get("id", "0")))
            except ValueError:
                pass
            self._redirect("/time?m=day_deleted")

        elif path == "/since/add":
            title = (form.get("title") or "").strip()
            when = (form.get("start_at") or "").strip()
            if not title:
                self._send(400, view_time(error="得给这件事起个名字。"))
                return
            try:
                date.fromisoformat(when)
            except ValueError:
                self._send(400, view_time(error="日期格式不对。"))
                return
            store.since_add(title, when, (form.get("note") or "").strip()[:120])
            self._redirect("/time?m=since_saved")

        elif path == "/since/delete":
            try:
                store.since_delete(int(form.get("id", "0")))
            except ValueError:
                pass
            self._redirect("/time?m=since_deleted")

        elif path == "/settings/auto":
            for key in ("auto_news", "auto_backup"):
                store.set_setting(key, "1" if form.get(key) == "1" else "0")
            hours = form.get("news_interval_hours", "6")
            if hours in ("1", "3", "6", "12", "24"):
                store.set_setting("news_interval_hours", hours)
            keep = form.get("backup_keep", "7")
            if keep in ("3", "7", "14", "30"):
                store.set_setting("backup_keep", keep)
            self._redirect("/settings?m=settings_saved")

        elif path == "/settings/backup":
            try:
                maintenance.run_backup(
                    keep=int(store.get_setting("backup_keep", "7") or 7))
                self._redirect("/settings?m=backup_done")
            except OSError as exc:
                self._send(400, view_settings(error=f"备份失败：{exc}"))

        elif path == "/settings/autostart":
            want = form.get("enable") == "1"
            ok, problem = toggle_autostart(want)
            if ok:
                self._redirect("/settings?m=" +
                               ("autostart_on" if want else "autostart_off"))
            else:
                self._send(400, view_settings(
                    error=f"改自启失败：{problem}。"
                          f"请用命令行：sudo systemctl "
                          f"{'enable' if want else 'disable'} {SERVICE_NAME}"))

        elif path == "/settings/port":
            raw = (form.get("port") or "").strip()
            try:
                new_port = int(raw)
            except ValueError:
                self._send(400, view_settings(error="端口得是数字。"))
                return
            if not (1024 <= new_port <= 65535):
                self._send(400, view_settings(
                    error="端口要在 1024~65535 之间（1024 以下需要 root）。"))
                return
            if new_port == PORT:
                self._redirect("/settings?m=settings_saved")
                return
            # 先把回应发出去，再换进程 —— 否则浏览器会看到连接被重置
            self._send(200, layout(
                f'<div class="card"><h3>已改到 {new_port} 端口</h3>'
                f'<div class="meta">服务正在重启，旧地址马上失效。</div>'
                f'<div class="meta" style="margin-top:8px">新地址：'
                f'http://这台机器的IP:{new_port}</div>'
                f'<a href="/" style="display:inline-block;margin-top:12px;'
                f'color:var(--accent-ink)">重新访问</a></div>', "settings"))
            threading.Thread(target=set_port, args=(new_port,),
                             daemon=True).start()
            return

        elif path == "/settings/clearcache":
            try:
                done = clear_cache()
            except OSError as exc:
                self._send(400, view_settings(error=f"清理失败：{exc}"))
                return
            self._redirect("/settings?m=cache_cleared")
            return

        elif path == "/settings/import":
            payload = form.get("payload") or ""
            if not payload.strip():
                self._send(400, view_settings(error="没有内容可导入。"))
                return
            count, problem = import_json(payload)
            if problem:
                self._send(400, view_settings(error=problem))
            else:
                self._redirect(f"/settings?m=imported&n={count}")

        elif path == "/notes/save":
            when = (form.get("d") or date.today().isoformat()).strip()
            try:
                date.fromisoformat(when)
            except ValueError:
                when = date.today().isoformat()
            body = (form.get("body") or "").strip()
            mood = (form.get("mood") or "").strip()
            if body or mood:
                store.note_add(when, mood, body)
            self._redirect(f"/notes?m=note_saved&d={quote(when)}")

        elif path == "/notes/update":
            try:
                note_id = int(form.get("id", "0"))
            except ValueError:
                note_id = 0
            when = (form.get("d") or date.today().isoformat()).strip()
            body = (form.get("body") or "").strip()
            mood = (form.get("mood") or "").strip()
            if note_id and (body or mood):
                store.note_update(note_id, mood, body)
            self._redirect(f"/notes?m=note_saved&d={quote(when)}")

        elif path == "/notes/delete":
            try:
                note_id = int(form.get("id", "0"))
            except ValueError:
                note_id = 0
            when = (form.get("d") or date.today().isoformat()).strip()
            if note_id:
                store.note_delete(note_id)
            self._redirect(f"/notes?m=note_deleted&d={quote(when)}")

        elif path == "/settings/save":
            store.set_setting(
                "site_title",
                (form.get("site_title") or "").strip()[:40] or "去往未来")
            theme = form.get("theme", "")
            if theme in themes.THEMES:
                store.set_setting("theme", theme)
            font = form.get("font", "")
            if font in themes.FONTS:
                store.set_setting("font", font)
            for key in ("home_quote", "home_days", "home_memories", "bg_motion"):
                store.set_setting(key, "1" if form.get(key) == "1" else "0")
            lang = form.get("quote_lang", "all")
            if lang in ("all", "zh", "en"):
                store.set_setting("quote_lang", lang)
            raw = (form.get("feeds") or "").strip()
            parsed = []
            for line in raw.splitlines():
                line = line.strip()
                if not line or "|" not in line:
                    continue
                name, _, url = line.partition("|")
                name, url = name.strip(), url.strip()
                if url.startswith("http"):
                    parsed.append({"name": name or url[:20], "url": url})
            feeds.save_feeds(parsed if parsed else list(feeds.DEFAULT_FEEDS))
            self._redirect("/settings?m=settings_saved")

        elif path == "/settings/password":
            old = form.get("old", "")
            new = form.get("new", "")
            confirm = form.get("confirm", "")
            if not check_password(old):
                self._send(400, view_settings(error="现在的密码不对。"))
                return
            if len(new) < 6:
                self._send(400, view_settings(error="新密码太短，至少 6 位。"))
                return
            if new != confirm:
                self._send(400, view_settings(error="两次输入的新密码不一样。"))
                return
            set_password(new)
            self._redirect("/settings?m=password_changed")

        else:
            self._send(404, layout('<p class="empty">这里什么都没有。</p>', ""))


_refresh_lock = threading.Lock()

EXPORT_TABLES = ("letters", "days", "since", "notes")


# ---------------------------------------------------------------- 管理：启动 / 缓存 / 卸载


def service_state():
    """读到服务状态，不需要 root。

    「运行中」是实际去连一下本机端口，不是无条件写 True —— 那个假检测
    会让页面永远显示"运行中"，看不出服务已经挂了。
    """
    unit_exists = os.path.exists(UNIT_PATH)

    running = False
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=1.5):
            running = True
    except OSError:
        running = False

    return {
        "unit_exists": unit_exists,
        "autostart": os.path.exists(WANTS_PATH),
        "running": running,
        "port": PORT,
    }


def cache_info():
    """缓存/垃圾有多大，给设置页显示。"""
    here = os.path.dirname(os.path.abspath(__file__))
    pycache = os.path.join(here, "__pycache__")
    pycache_size = 0
    pycache_files = 0
    if os.path.isdir(pycache):
        for name in os.listdir(pycache):
            full = os.path.join(pycache, name)
            if os.path.isfile(full):
                pycache_size += os.path.getsize(full)
                pycache_files += 1

    wal = 0
    for suffix in ("-wal", "-shm"):
        path = store.DB_PATH + suffix
        if os.path.exists(path):
            wal += os.path.getsize(path)

    backups = maintenance.list_backups()
    backup_size = sum(b["size_kb"] for b in backups) * 1024

    news_rows = store.news_count()
    db_size = os.path.getsize(store.DB_PATH) if os.path.exists(store.DB_PATH) else 0

    return {
        "pycache_kb": pycache_size / 1024,
        "pycache_files": pycache_files,
        "wal_kb": wal / 1024,
        "backup_count": len(backups),
        "backup_kb": backup_size / 1024,
        "news_rows": news_rows,
        "db_kb": db_size / 1024,
    }


def clear_cache(keep_backups=3, news_keep=80, vacuum=True):
    """清掉能安全清的东西。返回做了什么。

    只动三类：Python 的 __pycache__、超出保留数的旧备份、
    以及资讯表里超出条数的旧记录。不碰信件、手记、日子。
    """
    done = []
    here = os.path.dirname(os.path.abspath(__file__))

    # 1. __pycache__
    pycache = os.path.join(here, "__pycache__")
    if os.path.isdir(pycache):
        count = 0
        for name in os.listdir(pycache):
            full = os.path.join(pycache, name)
            if os.path.isfile(full):
                try:
                    os.remove(full)
                    count += 1
                except OSError:
                    pass
        if count:
            done.append(f"清掉 {count} 个 Python 缓存文件")

    # 2. 旧备份
    for stale in maintenance.list_backups()[max(1, keep_backups):]:
        try:
            os.remove(os.path.join(maintenance.backup_dir(), stale["name"]))
            done.append(f"删掉旧备份 {stale['name']}")
        except OSError:
            pass

    # 3. 资讯旧记录
    conn = store.connect()
    total = conn.execute("SELECT COUNT(*) AS n FROM news").fetchone()["n"]
    if total > news_keep:
        conn.execute(
            "DELETE FROM news WHERE id NOT IN ("
            "  SELECT id FROM news ORDER BY published DESC, id DESC LIMIT ?)",
            (news_keep,))
        conn.commit()
        done.append(f"资讯从 {total} 条裁剪到 {news_keep} 条")

    # 4. 合并 WAL，必要时瘦身数据库
    store.checkpoint()
    if vacuum:
        try:
            conn.execute("VACUUM")
            done.append("数据库已瘦身（VACUUM）")
        except sqlite3.Error:
            pass

    return done


CLI_HINTS = {
    "start": f"sudo systemctl start {SERVICE_NAME}",
    "stop": f"sudo systemctl stop {SERVICE_NAME}",
    "restart": f"sudo systemctl restart {SERVICE_NAME}",
    "autostart_on": f"sudo systemctl enable {SERVICE_NAME}",
    "autostart_off": f"sudo systemctl disable {SERVICE_NAME}",
    "status": f"sudo systemctl status {SERVICE_NAME}",
    "logs": f"sudo journalctl -u {SERVICE_NAME} -f",
    "clear_cache": "python3 app.py --clear-cache",
    "uninstall": "sudo bash install.sh --uninstall",
}


def set_port(new_port):
    """改端口并让进程自己重启。

    不用 systemctl：那需要 root。这里直接改配置、然后 os.execv 换成新进程，
    PID 不变，systemd 也认为是同一次运行，不会判成崩溃。
    """
    cfg = load_config()
    cfg["port"] = int(new_port)
    save_config(cfg)
    # 先回应网页，再换进程（顺序在调用处保证）
    argv = [sys.executable, os.path.abspath(__file__)] + sys.argv[1:]
    os.execv(sys.executable, argv)


def autostart_enabled():
    return os.path.exists(WANTS_PATH)


def toggle_autostart(enable):
    """开关开机自启。

    install.sh 会写好一条 sudoers 规则，只允许服务账户执行
    systemctl enable/disable future-letter。没装那条规则时会失败，
    调用方回退成"给出命令让用户自己敲"。
    """
    action = "enable" if enable else "disable"
    try:
        result = subprocess.run(
            ["sudo", "-n", "systemctl", action, SERVICE_NAME],
            capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return True, ""
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        return False, detail[-1] if detail else f"systemctl {action} 失败"
    except FileNotFoundError:
        return False, "这台机器没有 sudo"
    except subprocess.TimeoutExpired:
        return False, "命令超时"
    except OSError as exc:
        return False, str(exc)


def export_json():
    """把全部内容导成 JSON。信也在里面，注意保管。"""
    conn = store.connect()
    data = {"exported_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "version": 5, "site_title": site_title(), "tables": {}}
    for table in EXPORT_TABLES:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)).fetchone()
        if not exists:
            continue
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        data["tables"][table] = [dict(r) for r in rows]
    return json.dumps(data, ensure_ascii=False, indent=2)


def import_json(payload):
    """导入 JSON。只追加，不删现有内容，也不会重复导入同一条。

    信没有唯一约束，所以按 (标题, 正文, 解锁日) 判重；
    手记按日期判重；日子和「已经多久」按 (标题, 日期) 判重。
    """
    try:
        data = json.loads(payload)
    except ValueError:
        return 0, "不是合法的 JSON。"
    tables = data.get("tables") if isinstance(data, dict) else None
    if not isinstance(tables, dict):
        return 0, "里面没有 tables 字段，可能不是本站导出的文件。"

    conn = store.connect()
    total = 0
    skipped = 0

    def exists(table, where, values):
        row = conn.execute(
            f"SELECT 1 FROM {table} WHERE {where} LIMIT 1", values).fetchone()
        return row is not None

    try:
        for table in EXPORT_TABLES:
            rows = tables.get(table) or []
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                try:
                    if table == "letters":
                        if exists("letters",
                                  "title=? AND body=? AND unlock_at=?",
                                  (row.get("title"), row.get("body"),
                                   row.get("unlock_at"))):
                            skipped += 1
                            continue
                    elif table == "notes":
                        if exists("notes", "entry_date=?",
                                  (row.get("entry_date"),)):
                            skipped += 1
                            continue
                    elif table in ("days", "since"):
                        date_col = "date" if table == "days" else "start_at"
                        if exists(table, f"title=? AND {date_col}=?",
                                  (row.get("title"), row.get(date_col))):
                            skipped += 1
                            continue

                    cols = [c for c in row.keys() if c != "id"]
                    if not cols:
                        continue
                    placeholders = ",".join("?" for _ in cols)
                    conn.execute(
                        f"INSERT INTO {table} ({','.join(cols)}) "
                        f"VALUES ({placeholders})",
                        [row[c] for c in cols])
                    total += 1
                except sqlite3.Error:
                    skipped += 1
                    continue
        conn.commit()
    except sqlite3.Error as exc:
        return total, f"导入时出错：{exc}"

    if total == 0 and skipped:
        return 0, "这些内容都已经存在了，没有重复导入。"
    return total, ""


def _safe_refresh():
    if not _refresh_lock.acquire(blocking=False):
        return
    try:
        feeds.refresh_all()
    except Exception:  # noqa: BLE001
        pass
    finally:
        _refresh_lock.release()


def main(argv):
    if "--help" in argv or "-h" in argv or "help" in argv:
        print(HELP_TEXT)
        return 0

    store.init()
    migrate_legacy_password()

    if "--set-password" in argv:
        idx = argv.index("--set-password")
        if idx + 1 >= len(argv):
            print("用法: python3 app.py --set-password 新密码")
            return 2
        set_password(argv[idx + 1])
        print("密码已更新。")
        return 0

    if "--backup" in argv:
        idx = argv.index("--backup")
        target = argv[idx + 1] if idx + 1 < len(argv) else ""
        if not target:
            print("用法: python3 app.py --backup 目标路径.db")
            return 2
        size = store.backup_to(target)
        print(f"已备份到 {target}（{size / 1024:.0f} KB）")
        return 0

    if "--refresh-news" in argv:
        ok, failures = feeds.refresh_all()
        print(f"成功 {ok} 个源")
        for f in failures:
            print("  失败:", f)
        return 0

    # ---------- 命令行管理 ----------

    if "--status" in argv:
        svc = service_state()
        cache = cache_info()
        print("=== 服务 ===")
        print(f"  开机自启: {'已开启' if svc['autostart'] else '已关闭'}")
        print(f"  unit 文件: {'存在' if svc['unit_exists'] else '不存在'}")
        print(f"  端口:     {svc['port']}")
        print("=== 缓存 ===")
        print(f"  __pycache__: {cache['pycache_files']} 个文件 / "
              f"{cache['pycache_kb']:.0f} KB")
        print(f"  WAL:         {cache['wal_kb']:.0f} KB")
        print(f"  备份:        {cache['backup_count']} 份 / "
              f"{cache['backup_kb']:.0f} KB")
        print(f"  资讯:        {cache['news_rows']} 条")
        print(f"  数据库:      {cache['db_kb']:.0f} KB")
        print("=== 数据 ===")
        for name, value in store.stats().items():
            print(f"  {name}: {value} 行")
        return 0

    if "--clear-cache" in argv:
        keep = 3
        news_keep = 80
        # 允许 --clear-cache --keep 5 --news 100
        if "--keep" in argv:
            try:
                keep = int(argv[argv.index("--keep") + 1])
            except (IndexError, ValueError):
                pass
        if "--news" in argv:
            try:
                news_keep = int(argv[argv.index("--news") + 1])
            except (IndexError, ValueError):
                pass
        done = clear_cache(keep_backups=keep, news_keep=news_keep)
        if not done:
            print("没有可清理的东西。")
        for line in done:
            print("  " + line)
        return 0

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    # 让机器自己干活：定时抓资讯、每天备份、定期合并 WAL
    maintenance.start()
    print(f"{site_title()} 已启动: http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
