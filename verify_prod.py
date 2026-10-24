#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生产环境验收：页面、登录、令牌、移动端写法、服务器信息、真实抓取。"""

import gzip
import http.cookiejar
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://192.168.31.211:9000"
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else "weilai2026"

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

    def request(self, path, data=None, headers=None):
        body = urllib.parse.urlencode(data or {}).encode() if data is not None else None
        req = urllib.request.Request(
            BASE + path, data=body,
            method="POST" if data is not None else "GET",
            headers=headers or {})
        try:
            with self.opener.open(req, timeout=90) as resp:
                return (resp.status, resp.read().decode("utf-8", "replace"),
                        resp.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace"), e.headers


def main():
    anon = Client()
    code, body, _ = anon.request("/login")
    check("登录页", code == 200 and "密码" in body, str(code))

    for path in ("/", "/letters", "/news", "/time", "/notes", "/quotes",
                 "/settings"):
        code, _, _ = anon.request(path)
        check(f"未登录 {path} 跳登录", code == 303, str(code))

    me = Client()
    code, _, _ = me.request("/login", {"password": PASSWORD})
    check("密码登录成功", code == 303, str(code))
    if code != 303:
        print("\n登录失败，后续无法继续。")
        return 1

    pages = {
        "/": "dateline",
        "/letters": "信",
        "/time": "已经多久",
        "/notes": "今天的心情",
        "/quotes": "摘句",
        "/settings": "这台机器",
    }
    for path, marker in pages.items():
        code, body, _ = me.request(path)
        check(f"{path} 内容正确", code == 200 and marker in body, str(code))
    code, body, _ = me.request("/news")
    check("/news 内容正确", code == 200 and "资讯" in body, str(code))

    # 移除的页面
    for gone in ("/reading", "/courses", "/diary"):
        code, _, _ = me.request(gone)
        check(f"旧页面 {gone} 已 404", code == 404, str(code))

    # 表单令牌
    code, body, _ = me.request("/time")
    m = re.search(r'name="_tok" value="([^"]+)"', body)
    token = m.group(1) if m else ""
    check("页面带表单令牌", bool(token))
    code, _, _ = me.request("/days/add", {"title": "x", "date": "2026-12-01"})
    check("缺令牌被拒", code == 400, str(code))
    code, _, _ = me.request("/days/add",
                            {"title": "x", "date": "2026-12-01", "_tok": "bad"})
    check("错令牌被拒", code == 400, str(code))

    # 关键回归：Origin: null
    code, _, _ = me.request("/days/add",
                            {"title": "临时", "date": "2026-12-31",
                             "_tok": token},
                            headers={"Origin": "null"})
    check("【回归】Origin: null 可用（iOS 主屏/WebView）", code == 303, str(code))

    # 收拾掉刚才加的临时数据（卡片结构：标题在前，删除表单里的 id 在后）
    code, body, _ = me.request("/time")
    for block in re.findall(r'<div class="count-card[^"]*">.*?</form></div>', body, re.S):
        tm = re.search(r'<div class="t">([^<]*)</div>', block)
        im = re.search(r'name="id" value="(\d+)"', block)
        if tm and im and tm.group(1).strip() == "临时":
            me.request("/days/delete", {"id": im.group(1), "_tok": token})
    _, body, _ = me.request("/time")
    check("临时数据已清理", '<div class="t">临时</div>' not in body)

    # 已经多久
    code, _, _ = me.request("/since/add",
                            {"title": "验收临时项", "start_at": "2024-01-01",
                             "_tok": token})
    check("可以记「已经多久」", code == 303, str(code))
    code, body, _ = me.request("/time")
    check("显示年月日拆分", re.search(r"\d+ 年 \d+ 个月", body) is not None)
    check("显示总天数与小时", re.search(r"共 [\d,]+ 天", body) is not None)
    for block in re.findall(
            r'<div class="since-card[^"]*">.*?</form></div>', body, re.S):
        tm = re.search(r'<div class="t">([^<]*)</div>', block)
        im = re.search(r'name="id" value="(\d+)"', block)
        if tm and im and tm.group(1).strip() == "验收临时项":
            me.request("/since/delete", {"id": im.group(1), "_tok": token})
    _, body, _ = me.request("/time")
    check("临时「已经多久」已清理", "验收临时项" not in body)

    # 热力图
    _, body, _ = me.request("/notes")
    check("手记页有热力图", 'class="heat"' in body)
    check("热力图格子可点", "/notes?d=" in body)

    # 导出
    code, payload, hdrs = me.request("/export.json")
    check("可以导出 JSON", code == 200 and '"tables"' in payload, str(code))
    check("导出带下载名", "attachment" in (hdrs.get("Content-Disposition") or ""))

    # 后台维护与备份
    code, _, _ = me.request("/settings/auto",
                            {"auto_news": "1", "auto_backup": "1",
                             "news_interval_hours": "6",
                             "backup_keep": "7", "_tok": token})
    check("可以保存自动维护设置", code == 303, str(code))
    code, _, _ = me.request("/settings/backup", {"_tok": token})
    check("可以手动备份", code == 303, str(code))
    _, body, _ = me.request("/settings")
    check("设置页显示备份文件", "data-" in body)

    # 移动端写法
    code, body, hdrs = me.request("/static/style.css")
    if hdrs.get("Content-Encoding") == "gzip":
        body = gzip.decompress(body.encode("latin-1")).decode("utf-8")
    check("无 background-attachment（iOS 渐变错位）",
          not re.search(r"background-attachment\s*:\s*fixed\s*;", body))
    check("输入框字号 16px", "font-size:16px" in body)
    check("导航可滑动", "overflow-x:auto" in body)
    check("触控区 ≥44px", "min-height:44px" in body)
    check("主题 :has() 选中态", ":has(input:checked)" in body)

    # 三个主题
    colors = {}
    for theme in ("impression", "paper", "night"):
        _, css, _ = me.request(f"/static/style.css?t={theme}")
        m = re.search(r"--bg:(#[0-9a-fA-F]+)", css)
        colors[theme] = m.group(1) if m else None
    check("三套主题底色不同", len(set(colors.values())) == 3, str(colors))

    # 摘句
    _, body, _ = me.request("/quotes")
    m = re.search(r"共 (\d+) 句", body)
    total = int(m.group(1)) if m else 0
    check(f"摘句 {total} 句（≥200）", total >= 200, str(total))
    _, second, _ = me.request("/quotes?n=1")
    check("换一句可用", second != body)

    # 服务器信息
    _, body, _ = me.request("/settings")
    check("显示主机名", "armbian" in body)
    check("显示 CPU 温度", "°C" in body)
    check("显示内存", "MB" in body)
    check("显示本程序内存", "本程序内存" in body)

    # 性能
    code, _, hdrs = me.request("/", headers={"Accept-Encoding": "gzip"})
    check("首页 gzip", hdrs.get("Content-Encoding") == "gzip")
    etag = hdrs.get("ETag")
    code, _, _ = me.request("/", headers={"If-None-Match": etag or "",
                                         "Accept-Encoding": "gzip"})
    check("二次访问 304", code == 304, str(code))
    _, _, hdrs = me.request("/", headers={"Accept-Encoding": "gzip"})
    size = int(hdrs.get("Content-Length") or 0)
    check(f"首页仅 {size} 字节", size < 4096, str(size))

    # 真实抓取
    print("  正在抓取资讯（最多等 60 秒）…")
    t0 = time.time()
    code, body, _ = me.request("/news/refresh", {"_tok": token})
    elapsed = time.time() - t0
    check(f"资讯刷新（{elapsed:.1f}s）", code in (200, 303), str(code))
    _, body, _ = me.request("/news")
    sources = [s for s in ("36氪", "少数派", "Solidot", "IT之家", "开源中国")
               if s in body]
    check(f"抓到 {len(sources)} 个真实来源", len(sources) >= 2, str(sources))

    me.request("/logout")
    check("退出登录", True)

    print()
    if failures:
        print(f"FAILED ({len(failures)}): " + "; ".join(failures))
        return 1
    print("ALL PRODUCTION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
