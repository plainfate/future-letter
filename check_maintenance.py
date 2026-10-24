#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""看后台维护到底做了什么。"""

import os
import sys

sys.path.insert(0, "/opt/future-letter")

import maintenance  # noqa: E402
import store        # noqa: E402

store.init()

print("=== 维护状态 ===")
for key, value in maintenance.state().items():
    if key in ("thread", "stop_event"):
        continue
    print(f"  {key:<14} {value}")

print("\n=== 备份 ===")
for b in maintenance.list_backups():
    print(f"  {b['name']}  {b['size_kb']:.0f} KB  {b['mtime']}")

print("\n=== 现在手动跑一轮 ===")
for item in maintenance.tick():
    print("  " + item)

print("\n=== 跑完再看状态 ===")
st = maintenance.state()
print(f"  上次抓资讯: {st.get('last_news')}")
print(f"  上次备份:   {st.get('last_backup')}")
print(f"  资讯成功源: {st.get('news_ok')}")
if st.get("errors"):
    print("  出错记录:")
    for e in st["errors"]:
        print("    " + e)
else:
    print("  没有出错")

print("\n=== 磁盘占用 ===")
total = 0
d = maintenance.backup_dir()
for name in os.listdir(d):
    full = os.path.join(d, name)
    if os.path.isfile(full):
        total += os.path.getsize(full)
print(f"  备份目录共 {total/1024:.0f} KB")
print(f"  数据库 {os.path.getsize(store.DB_PATH)/1024:.0f} KB")
