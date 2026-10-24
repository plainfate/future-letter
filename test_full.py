#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站测试：功能、安全、移动端、性能机制。

重点覆盖这几件真出过问题的事：
  · Origin: null（iOS 主屏 / 安卓 WebView）不能被误判成跨站；
  · 没有令牌的表单必须被拒；
  · 提交后必须重定向，刷新不能重复提交；
  · CSS 里不能有 iOS 会渲染错乱的写法，输入框字号必须 ≥16px。
"""

import gzip
import http.cookiejar
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

PORT = 18094
BASE = f"http://127.0.0.1:{PORT}"
MODULES = ["app.py", "store.py", "feeds.py", "lunar.py", "themes.py",
           "quotes.py", "sysinfo.py", "heatmap.py", "elapsed.py",
           "maintenance.py"]
SECRET_FUTURE = "FUTURE-SECRET-QQ7"
SECRET_PAST = "PAST-BODY-ZZ3"

failures = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name
          + (f"  [{detail}]" if detail and not ok else ""))
    if not ok:
        failures.append(name)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar), NoRedirect())

    def request(self, path, data=None, headers=None, raw=False):
        body = urllib.parse.urlencode(data or {}).encode() if data is not None else None
        method = "POST" if data is not None else "GET"
        req = urllib.request.Request(BASE + path, data=body, method=method,
                                     headers=headers or {})
        try:
            with self.opener.open(req, timeout=20) as resp:
                payload = resp.read()
                return (resp.status,
                        "" if raw else payload.decode("utf-8", "replace"),
                        resp.headers, payload)
        except urllib.error.HTTPError as e:
            payload = e.read()
            return (e.code, "" if raw else payload.decode("utf-8", "replace"),
                    e.headers, payload)
        except Exception as exc:  # 超时之类
            print(f"    请求失败: {method} {path} 头={headers} → "
                  f"{type(exc).__name__}: {exc}")
            raise


def wait_up(timeout=40):
    for _ in range(timeout * 5):
        try:
            with urllib.request.urlopen(BASE + "/login", timeout=1):
                return True
        except Exception:
            time.sleep(0.2)
    return False


def get_token(body):
    m = re.search(r'name="_tok" value="([^"]+)"', body)
    return m.group(1) if m else None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    tmp = tempfile.mkdtemp(prefix="fl_v4_")
    for m in MODULES:
        shutil.copy(os.path.join(here, m), os.path.join(tmp, m))
    with open(os.path.join(tmp, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"port": PORT}, f)
    subprocess.run([sys.executable, "app.py", "--set-password", "testpw123"],
                   cwd=tmp, check=True, capture_output=True)

    log_path = os.path.join(tmp, "server.log")
    log_file = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=tmp,
                            stdout=log_file, stderr=subprocess.STDOUT)
    try:
        if not wait_up():
            print("服务没起来")
            log_file.close()
            with open(log_path, encoding="utf-8", errors="replace") as f:
                print(f.read()[-2500:])
            return 1

        anon = Client()
        code, body, _, _ = anon.request("/login")
        check("登录页", code == 200 and "密码" in body, str(code))

        pages = ["/", "/letters", "/news", "/time", "/notes", "/quotes", "/settings"]
        for path in pages:
            code, _, hdrs, _ = anon.request(path)
            check(f"未登录 {path} 跳登录",
                  code == 303 and hdrs.get("Location") == "/login", str(code))

        me = Client()
        code, _, hdrs, _ = me.request("/login", {"password": "testpw123"})
        check("登录成功", code == 303 and any(c.name == "fy_sid" for c in me.jar),
              str(code))

        # ---------- 每页能开 ----------
        markers = {
            "/": "dateline",
            "/letters": "信",
            "/time": "已经多久",
            "/notes": "写点什么",
            "/quotes": "摘句",
            "/settings": "配色",
        }
        for path, marker in markers.items():
            code, body, _, _ = me.request(path)
            check(f"{path} 可访问", code == 200 and marker in body, str(code))
        code, body, _, _ = me.request("/news")
        check("/news 可访问", code == 200 and "资讯" in body, str(code))

        # 旧路径 /days 仍可用（别让收藏夹失效）
        code, body, _, _ = me.request("/days")
        check("旧路径 /days 兼容", code == 200 and "已经多久" in body, str(code))

        # ---------- 待读确实没了 ----------
        for gone in ("/reading", "/reading/add", "/courses", "/diary"):
            code, _, _, _ = me.request(gone)
            check(f"已移除 {gone}（404）", code == 404, str(code))

        # ---------- 表单令牌 ----------
        print("  ---- 表单令牌与跨设备 ----")
        code, body, _, _ = me.request("/time")
        token = get_token(body)
        check("页面带表单令牌", bool(token), str(token))

        code, body, _, _ = me.request("/days/add",
                                      {"title": "无令牌", "date": "2026-12-01"})
        check("缺令牌被拒（400）", code == 400, str(code))
        check("拒绝时提示刷新", "刷新" in body)

        code, _, _, _ = me.request("/days/add",
                                   {"title": "错令牌", "date": "2026-12-01",
                                    "_tok": "deadbeef" * 4})
        check("错令牌被拒（400）", code == 400, str(code))

        # 关键回归：Origin: null 必须放行（iOS 主屏 / WebView）
        code, _, hdrs, _ = me.request(
            "/days/add",
            {"title": "主屏测试", "date": "2026-12-02", "_tok": token or ""},
            headers={"Origin": "null"})
        check("【回归】Origin: null 不再被误杀", code == 303,
              f"{code} ← 主屏/WebView 用户会卡在这")

        # 其他设备常见情形
        for origin in ("http://localhost:8899", "http://192.168.1.50:9000"):
            code, _, _, _ = me.request(
                "/days/add",
                {"title": "别的设备", "date": "2026-12-03", "_tok": token or ""},
                headers={"Origin": origin})
            check(f"Origin {origin} 可用", code == 303, str(code))

        # ---------- 提交后必须重定向（刷新不重复提交） ----------
        code, _, hdrs, _ = me.request(
            "/days/add",
            {"title": "重定向测试", "date": "2026-12-04", "_tok": token or ""})
        check("提交后 303 重定向", code == 303, str(code))
        check("重定向目标带提示码",
              "m=" in (hdrs.get("Location") or ""), str(hdrs.get("Location")))

        code, body, _, _ = me.request("/time?m=day_saved")
        check("提示语正确显示", "日子已记下" in body)

        # ---------- 信 ----------
        future = (date.today() + timedelta(days=30)).isoformat()
        past = (date.today() - timedelta(days=3)).isoformat()
        me.request("/new", {"title": "给未来的我", "body": SECRET_FUTURE,
                            "unlock_at": future, "_tok": token or ""})
        me.request("/new", {"title": "已经过期了", "body": SECRET_PAST,
                            "unlock_at": past, "_tok": token or ""})
        code, body, _, _ = me.request("/letters")
        check("信列表显示两封", "给未来的我" in body and "已经过期了" in body)
        check("未解锁信有倒计时", bool(re.search(r"还有 \d+ 天", body)))
        check("【安全】列表不含未解锁正文", SECRET_FUTURE not in body)

        code, body, _, _ = me.request("/letter?id=1")
        check("未解锁信显示封存页", "还没到打开的时候" in body, str(code))
        check("【安全】封存页不含正文", SECRET_FUTURE not in body)
        code, body, _, _ = me.request("/letter?id=2")
        check("已解锁信可读正文", SECRET_PAST in body, str(code))

        code, body, _, _ = me.request("/new")
        check("写信页带令牌", get_token(body) is not None)

        # ---------- 手记 ----------
        today = date.today().isoformat()
        me.request("/notes/save", {"d": today, "mood": "🙂",
                                   "body": "今天写完了整个站。",
                                   "_tok": token or ""})
        code, body, _, _ = me.request("/notes")
        check("手记可保存", "今天写完了整个站" in body, str(code))

        # 一天写多条（这是以前的 bug：entry_date 有 UNIQUE）
        me.request("/notes/save", {"d": today, "mood": "😐",
                                   "body": "中午又想到一件事。",
                                   "_tok": token or ""})
        me.request("/notes/save", {"d": today, "mood": "😴",
                                   "body": "晚上第三条。",
                                   "_tok": token or ""})
        _, body, _, _ = me.request(f"/notes?d={today}")
        items = body.count('class="note-item"')
        check(f"一天能写多条（现有 {items} 条）", items >= 3, str(items))
        check("三条正文都在",
              "今天写完了整个站" in body and "中午又想到一件事" in body
              and "晚上第三条" in body)
        check("有编辑入口", "edit=" in body and "编辑" in body)
        check("有「写过的日子」", "写过的日子" in body)

        # 编辑其中一条
        import re as _re
        ids = _re.findall(r'href="/notes\?d=[^"]*&amp;edit=(\d+)"', body)
        if ids:
            code, _, hdrs, _ = me.request("/notes/update", {
                "id": ids[0], "d": today, "mood": "😊",
                "body": "这条被改过了。", "_tok": token or ""})
            check("可以编辑某一条", code == 303, str(code))
            _, body2, _, _ = me.request(f"/notes?d={today}")
            check("编辑生效", "这条被改过了" in body2)

        # 删除不影响其它条
        me.request("/notes/delete", {"id": ids[0] if ids else "1",
                                     "d": today, "_tok": token or ""})
        _, body3, _, _ = me.request(f"/notes?d={today}")
        check("删一条后其它还在",
              body3.count('class="note-item"') == items - 1,
              f"{body3.count('class=\"note-item\"')} vs {items - 1}")

        old_day = (date.today() - timedelta(days=365)).isoformat()
        me.request("/notes/save", {"d": old_day, "mood": "😊",
                                   "body": "一年前的同一天。", "_tok": token or ""})
        _, body, _, _ = me.request("/")
        check("首页出现「往年这天」",
              "往年这天" in body and "一年前的同一天" in body)

        # ---------- 手记里的热力图 ----------
        print("  ---- 热力图与已经多久 ----")
        code, body, _, _ = me.request("/notes")
        check("手记页有热力图", 'class="heat"' in body, str(code))
        check("热力图有格子", body.count('class="l') >= 100,
              str(body.count('class="l')))
        check("热力图有连续天数", "连着写了" in body or "今天还没写" in body
              or "还没有记录" in body)
        check("热力图格子可点进当天", "/notes?d=" in body)

        # ---------- 已经多久 ----------
        code, body, _, _ = me.request("/time")
        check("时间页有「已经多久」", "已经多久" in body, str(code))

        code, _, hdrs, _ = me.request("/since/add",
                                      {"title": "搬来这座城市",
                                       "start_at": "2023-06-01",
                                       "note": "拖着两个箱子",
                                       "_tok": token or ""})
        check("可以记「已经多久」", code == 303, str(code))
        code, body, _, _ = me.request("/time")
        check("显示已过多久", "搬来这座城市" in body and "since-card" in body,
              str(code))
        check("显示年月日拆分", re.search(r"\d+ 年 \d+ 个月", body) is not None)
        check("显示总天数", re.search(r"共 \d+ 天", body) is not None)

        m = re.search(r'name="id" value="(\d+)"', body)
        if m:
            code, _, _, _ = me.request("/since/delete",
                                       {"id": m.group(1), "_tok": token or ""})
            check("可以删掉「已经多久」", code == 303, str(code))

        # 未来的日期应该显示「还有」
        me.request("/since/add", {"title": "毕业", "start_at": "2030-06-01",
                                  "_tok": token or ""})
        _, body, _, _ = me.request("/time")
        check("未来日期显示「还有」", "还有" in body)

        # ---------- 导入导出 ----------
        print("  ---- 导出与导入 ----")
        code, payload, hdrs, _ = me.request("/export.json")
        check("可以导出 JSON", code == 200 and '"tables"' in payload, str(code))
        check("导出带下载文件名",
              "attachment" in (hdrs.get("Content-Disposition") or ""))
        exported = json.loads(payload)
        check("导出含信与手记",
              bool(exported["tables"].get("letters")) and
              bool(exported["tables"].get("notes")),
              str(list(exported["tables"].keys())))
        check("【安全】导出的信里确实有正文", SECRET_PAST in payload or
              SECRET_FUTURE in payload)

        code, body, _, _ = me.request("/settings/import",
                                      {"payload": payload, "_tok": token or ""})
        check("重复导入被识别", code in (303, 400), str(code))
        _, body, _, _ = me.request("/letters")
        check("重复导入没让信翻倍", body.count("给未来的我") == 1,
              str(body.count("给未来的我")))

        # ---------- 自动维护设置 ----------
        print("  ---- 后台维护 ----")
        code, _, _, _ = me.request("/settings/auto",
                                   {"auto_news": "1", "auto_backup": "1",
                                    "news_interval_hours": "3",
                                    "backup_keep": "7",
                                    "_tok": token or ""})
        check("可以保存自动维护设置", code == 303, str(code))

        code, _, _, _ = me.request("/settings/backup", {"_tok": token or ""})
        check("可以手动备份", code == 303, str(code))

        code, body, _, _ = me.request("/settings")
        check("设置页显示备份列表", "data-" in body or "还没有自动备份" in body)

        # ---------- 首页模块开关 ----------
        me.request("/settings/save", {"site_title": "去往未来", "theme": "paper",
                                      "feeds": "", "home_quote": "1",
                                      "home_days": "1", "home_memories": "1",
                                      "quote_lang": "all", "_tok": token or ""})
        _, body_on, _, _ = me.request("/")
        me.request("/settings/save", {"site_title": "去往未来", "theme": "paper",
                                      "feeds": "", "quote_lang": "all",
                                      "_tok": token or ""})
        _, body_off, _, _ = me.request("/")
        check("关掉模块后首页变短",
              len(body_off) < len(body_on),
              f"{len(body_off)} vs {len(body_on)}")
        check("关掉后摘句不再出现", "lang-tag" not in body_off)

        # 恢复
        me.request("/settings/save", {"site_title": "去往未来", "theme": "paper",
                                      "feeds": "", "home_quote": "1",
                                      "home_days": "1", "home_memories": "1",
                                      "quote_lang": "all", "_tok": token or ""})

        # ---------- 摘句 ----------
        code, body, _, _ = me.request("/quotes")
        check("摘句页可访问", code == 200 and "摘句" in body, str(code))
        m = re.search(r"共 (\d+) 句", body)
        total = int(m.group(1)) if m else 0
        check(f"摘句数量充足（{total} 句 ≥ 200）", total >= 200, str(total))

        code, body_next, _, _ = me.request("/quotes?n=1")
        check("「换一句」有效", code == 200 and body_next != body)
        _, body_zh, _, _ = me.request("/quotes?lang=zh")
        _, body_en, _, _ = me.request("/quotes?lang=en")
        check("中英筛选不同", body_zh != body_en)
        _, again, _, _ = me.request("/quotes")
        check("同一天摘句固定", again == body)

        # ---------- 设置 ----------
        code, body, _, _ = me.request("/settings")
        check("设置页有主题选择", "theme-pick" in body and "印象派" in body)
        check("设置页有改密码", 'action="/settings/password"' in body)
        check("设置页有服务器信息", "这台机器" in body and "CPU 核心" in body)
        check("主题选中态用 :has()", body.count("radio") >= 3)

        me.request("/settings/save", {"site_title": "我的未来", "theme": "paper",
                                      "feeds": "", "_tok": token or ""})
        _, body, _, _ = me.request("/")
        check("改站点名生效", "我的未来" in body)
        check("换主题后引用新样式表", "/static/style.css?t=paper" in body)

        # 三个主题的 CSS 都要能取到且颜色不同
        colors = {}
        for theme in ("impression", "paper", "night"):
            code, css, _, _ = me.request(f"/static/style.css?t={theme}")
            m = re.search(r"--bg:(#[0-9a-fA-F]+)", css)
            colors[theme] = m.group(1) if m else None
            check(f"{theme} 主题 CSS 可取", code == 200 and m is not None, str(code))
        check("三套主题底色各不相同",
              len(set(colors.values())) == 3, str(colors))

        # ---------- 改密码 ----------
        code, body, _, _ = me.request("/settings/password", {
            "old": "wrong", "new": "abcdef", "confirm": "abcdef",
            "_tok": token or ""})
        check("旧密码错时拒绝", code == 400 and "不对" in body, str(code))
        code, body, _, _ = me.request("/settings/password", {
            "old": "testpw123", "new": "abc", "confirm": "abc",
            "_tok": token or ""})
        check("新密码太短被拒", code == 400 and "太短" in body, str(code))
        code, body, _, _ = me.request("/settings/password", {
            "old": "testpw123", "new": "brandnew99", "confirm": "x",
            "_tok": token or ""})
        check("两次不一致被拒", code == 400 and "不一样" in body, str(code))
        code, _, _, _ = me.request("/settings/password", {
            "old": "testpw123", "new": "brandnew99", "confirm": "brandnew99",
            "_tok": token or ""})
        check("改密码成功并重定向", code == 303, str(code))

        other = Client()
        code, _, _, _ = other.request("/login", {"password": "testpw123"})
        check("旧密码失效", code == 401, str(code))
        code, _, _, _ = other.request("/login", {"password": "brandnew99"})
        check("新密码可登录", code == 303, str(code))

        # ---------- 移动端 CSS ----------
        print("  ---- 移动端 ----")
        _, css, _, _ = me.request("/static/style.css")
        # 只找真正生效的声明（注释里的词不算），加个分号确保是声明
        check("【回归】没有 background-attachment 声明（iOS 渐变错位）",
              not re.search(r"background-attachment\s*:\s*fixed\s*;", css))
        check("输入框字号 ≥16px（iOS 不自动放大）",
              bool(re.search(r"input,textarea,select\{[^}]*font-size:16px", css)))
        check("导航可横向滑动", "overflow-x:auto" in css)
        check("导航点击区 ≥44px", "min-height:44px" in css)
        check("按钮点击区 ≥44px",
              bool(re.search(r"button\{[^}]*min-height:44px", css)))
        check("主题选中态不依赖 JS class", ":has(input:checked)" in css)
        check("viewport 带 viewport-fit=cover", "viewport-fit=cover" in
              me.request("/")[1])

        # ---------- 性能机制 ----------
        print("  ---- 性能 ----")
        code, _, hdrs, raw = me.request("/", headers={"Accept-Encoding": "gzip"})
        check("HTML 走 gzip", hdrs.get("Content-Encoding") == "gzip",
              str(hdrs.get("Content-Encoding")))
        if hdrs.get("Content-Encoding") == "gzip":
            check("gzip 能还原", "dateline" in gzip.decompress(raw).decode("utf-8"))

        etag = hdrs.get("ETag")
        code, _, _, raw2 = me.request("/", headers={"If-None-Match": etag or "",
                                                    "Accept-Encoding": "gzip"})
        check("ETag 命中 304", code == 304, str(code))
        check("304 无正文", len(raw2) == 0)

        code, _, hdrs, raw_css = me.request("/static/style.css", raw=True,
                                            headers={"Accept-Encoding": "gzip"})
        css_plain = (gzip.decompress(raw_css).decode("utf-8")
                     if hdrs.get("Content-Encoding") == "gzip"
                     else raw_css.decode("utf-8"))
        check("CSS 长缓存",
              "max-age=31536000" in (hdrs.get("Cache-Control") or ""))
        check(f"CSS 压缩后 {len(raw_css)/1024:.1f} KB",
              len(raw_css) < len(css_plain.encode()) * 0.6)

        _, body, _, _ = me.request("/")
        check("页面不内联 CSS", "<style>" not in body)

        # ---------- 退出 ----------
        code, _, _, _ = me.request("/logout")
        check("退出登录", code == 303, str(code))
        code, _, _, _ = Client().request("/")
        check("退出后要求登录", code == 303, str(code))

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=6)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=6)
        log_file.close()
        with open(log_path, encoding="utf-8", errors="replace") as f:
            log = f.read()
        if failures:
            print("\n=== 服务端日志（末尾 25 行） ===")
            for line in log.strip().splitlines()[-25:]:
                print("  " + line)
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED ({len(failures)}): " + "; ".join(failures))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
