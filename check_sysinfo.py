#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确认设置页里的服务器信息是真的读到了（在服务器上跑）。"""

import re
import sys

sys.path.insert(0, "/opt/future-letter")

import app      # noqa: E402
import store    # noqa: E402
import sysinfo  # noqa: E402

store.init()
print("=== sysinfo.collect() 原始值 ===")
for k, v in sysinfo.collect(store.DB_PATH).items():
    if isinstance(v, float):
        v = f"{v:.1f}"
    print(f"  {k:<14} {v}")

print()
print("=== 设置页里渲染出来的格子 ===")
html = app.view_settings()
grid = re.search(r'<div class="sys-grid">(.*?)</div>\s*<h2', html, re.S)
if not grid:
    print("  找不到 sys-grid！")
    sys.exit(1)
cells = re.findall(r'<div class="k">(.*?)</div><div class="v">(.*?)</div>', grid.group(1))
for key, value in cells:
    text = re.sub(r"<[^>]+>", "", value).strip()
    print(f"  {key:<10} {text}")

print()
print("=== 检查有没有 '未知' 或 '—' ===")
missing = [(k, re.sub(r"<[^>]+>", "", v).strip())
           for k, v in cells
           if re.sub(r"<[^>]+>", "", v).strip() in ("未知", "—", "None")]
if missing:
    print("  读不到的项：", missing)
else:
    print("  全部读到了真实值")
