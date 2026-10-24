#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时换一个已知密码做验收，结束后把原密码哈希原样还原。

用法：
  python3 verify_with_temp_password.py before   # 备份并设置临时密码
  python3 verify_with_temp_password.py after    # 还原原密码
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, "/opt/future-letter")

import app      # noqa: E402
import store    # noqa: E402

BACKUP = "/opt/future-letter/.pw-restore.json"
TEMP_PASSWORD = "temp-verify-9917"


def check_still_valid():
    salt = store.get_setting("password_salt")
    return bool(salt and store.get_setting("password_hash"))


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "before"
    store.init()

    if action == "before":
        if os.path.exists(BACKUP):
            print("已经存在还原文件，先手动确认：", BACKUP)
            return 1
        original = {
            "salt": store.get_setting("password_salt"),
            "hash": store.get_setting("password_hash"),
        }
        if not original["hash"]:
            print("生产库里没有密码哈希，不能这样操作")
            return 1
        with open(BACKUP, "w", encoding="utf-8") as f:
            json.dump(original, f)
        os.chmod(BACKUP, 0o600)
        app.set_password(TEMP_PASSWORD)
        print(f"已备份原密码哈希，并设为临时密码 {TEMP_PASSWORD}")
        print("验收完请立刻运行：", sys.argv[0], "after")
        return 0

    if action == "after":
        if not os.path.exists(BACKUP):
            print("找不到还原文件，无法还原")
            return 1
        with open(BACKUP, encoding="utf-8") as f:
            original = json.load(f)
        store.set_setting("password_salt", original["salt"])
        store.set_setting("password_hash", original["hash"])
        os.remove(BACKUP)

        # 立刻验证还原成功：原哈希必须和当前一致
        ok = (store.get_setting("password_salt") == original["salt"] and
              store.get_setting("password_hash") == original["hash"])
        print("原密码已还原:" , ok)
        if not ok:
            print("!! 还原失败，请手动检查", BACKUP)
            return 1
        return 0

    print("用法: before | after")
    return 2


if __name__ == "__main__":
    sys.exit(main())
