#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在服务器上校验备份文件是否完整可用。"""

import sqlite3
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/backup-test.db"
conn = sqlite3.connect(path)
tables = sorted(r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"))
print("表:", ", ".join(tables))
for t in ("letters", "days", "notes", "reading", "news", "settings"):
    if t in tables:
        n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} 行")
print("完整性检查:", conn.execute("PRAGMA integrity_check").fetchone()[0])
conn.close()
