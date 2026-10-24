#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测每个页面的真实体积与耗时（含 gzip 对比）。"""

import gzip
import http.cookiejar
import sys
import time
import urllib.parse
import urllib.request
import zlib

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://192.168.31.211:9000"
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else "weilai2026"
PAGES = ["", "news", "letters", "time", "notes", "quotes", "settings"]

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

data = urllib.parse.urlencode({"password": PASSWORD}).encode()
try:
    opener.open(urllib.request.Request(BASE + "/login", data=data, method="POST"))
except urllib.error.HTTPError as err:
    if err.code != 303:
        print(f"登录失败（{err.code}）—— 密码不对？用法：")
        print("  python measure.py http://192.168.31.211:9000 你的密码")
        raise SystemExit(2)
else:
    print("提示：登录没有返回 303，可能密码不对，下面的数据不可信\n")

GZ = {"Accept-Encoding": "gzip"}


def fetch(url, headers=None):
    t0 = time.perf_counter()
    try:
        with opener.open(urllib.request.Request(url, headers=headers or {})) as resp:
            raw = resp.read()
            return resp.status, raw, resp.headers, (time.perf_counter() - t0) * 1000
    except urllib.error.HTTPError as err:  # 304 也会走这里
        return err.code, err.read(), err.headers, (time.perf_counter() - t0) * 1000


print(f"{'page':<12}{'status':<8}{'传输 KB':<11}{'解压后 KB':<12}{'耗时 ms':<10}")
print("-" * 55)
total_wire = 0
total_raw = 0
times = []
for page in PAGES:
    status, raw, hdrs, elapsed = fetch(BASE + "/" + page, GZ)
    wire = len(raw)
    plain = len(gzip.decompress(raw)) if hdrs.get("Content-Encoding") == "gzip" else wire
    total_wire += wire
    total_raw += plain
    times.append(elapsed)
    print(f"{page or 'today':<12}{status:<8}{wire/1024:<11.1f}{plain/1024:<12.1f}"
          f"{elapsed:<10.1f}")

print("-" * 55)
print(f"{'合计':<12}{'':<8}{total_wire/1024:<11.1f}{total_raw/1024:<12.1f}"
      f"{sum(times):<10.1f}")
print(f"\n平均耗时 {sum(times)/len(times):.1f} ms")
print(f"实际传输 {total_wire/1024:.1f} KB（未压缩是 {total_raw/1024:.1f} KB，"
      f"省了 {(1-total_wire/total_raw)*100:.0f}%）")

# 第二次请求：验证 ETag 让页面变成 304
status, raw, hdrs, elapsed = fetch(BASE + "/letters", GZ)
etag = hdrs.get("ETag")
status2, raw2, hdrs2, elapsed2 = fetch(BASE + "/letters",
                                       {**GZ, "If-None-Match": etag or ""})
print(f"\n缓存验证：首次 {elapsed:.1f} ms / {len(raw)} 字节 → "
      f"再次 {status2} / {len(raw2)} 字节 / {elapsed2:.1f} ms")

# CSS 单独一次
status, raw, hdrs, elapsed = fetch(BASE + "/static/style.css", GZ)
print(f"样式表：{status} / {len(raw)} 字节（gzip）/ {elapsed:.1f} ms / "
      f"{hdrs.get('Cache-Control')}")


# 再测一次，看有没有缓存效果
t0 = time.perf_counter()
with opener.open(urllib.request.Request(BASE + "/letters")) as resp:
    resp.read()
print(f"第二次请求 /letters：{(time.perf_counter()-t0)*1000:.1f} ms")
