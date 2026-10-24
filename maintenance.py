#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""后台维护：让这台机器自己干活，而不是只等人来点。

做三件事：
  1. 定时抓新闻（间隔可在设置里改）；
  2. 每天自动备份数据库，保留最近 N 份（解决"只有一份副本"的问题）；
  3. 定期把 WAL 合并回主库，别让它一直涨。

跑在一个后台线程里，不阻塞任何请求。所有开关都在设置页。
"""

import os
import sys
import threading
import time
from datetime import datetime, timedelta

import store

CHECK_INTERVAL = 300          # 每 5 分钟看一次该做什么

_state = {
    "started_at": None,
    "last_news": None,
    "last_backup": None,
    "last_checkpoint": None,
    "news_ok": 0,
    "backup_path": None,
    "errors": [],
}


def _record_error(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    _state["errors"].append(f"{stamp} {message}")
    _state["errors"] = _state["errors"][-10:]
    _log("出错: " + message)


def _log(message):
    """写一行日志到 stderr，systemd 会收进 journal，方便外部观察。"""
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"[维护 {stamp}] {message}", file=sys.stderr, flush=True)


def state():
    """给设置页看的运行状态。"""
    return dict(_state)


def _setting_int(key, default):
    try:
        return int(store.get_setting(key, str(default)))
    except (TypeError, ValueError):
        return default


def _setting_bool(key, default=False):
    raw = store.get_setting(key, "1" if default else "0")
    return raw == "1"


def backup_dir():
    base = os.path.dirname(os.path.abspath(store.DB_PATH))
    path = os.path.join(base, "backups")
    os.makedirs(path, exist_ok=True)
    return path


def run_backup(keep=7):
    """备份一次，然后删掉超出保留份数的旧备份。返回备份文件路径。"""
    directory = backup_dir()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = os.path.join(directory, f"data-{stamp}.db")
    store.backup_to(target)
    _state["backup_path"] = target
    _state["last_backup"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    files = sorted(
        (f for f in os.listdir(directory) if f.startswith("data-") and
         f.endswith(".db")),
        reverse=True)
    for stale in files[max(1, keep):]:
        try:
            os.remove(os.path.join(directory, stale))
        except OSError:
            pass
    return target


def list_backups():
    directory = backup_dir()
    out = []
    for name in sorted(os.listdir(directory), reverse=True):
        if not (name.startswith("data-") and name.endswith(".db")):
            continue
        full = os.path.join(directory, name)
        try:
            size = os.path.getsize(full)
        except OSError:
            continue
        out.append({"name": name, "size_kb": size / 1024,
                    "mtime": datetime.fromtimestamp(
                        os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M")})
    return out


def _due(last, hours):
    if not last:
        return True
    try:
        when = datetime.strptime(last, "%Y-%m-%d %H:%M")
    except ValueError:
        return True
    return datetime.now() - when >= timedelta(hours=hours)


def tick():
    """做一轮检查，只做该做的。返回这一轮做了什么（测试用）。"""
    did = []

    # 1. 新闻：按设置的间隔刷新
    if _setting_bool("auto_news", True):
        hours = _setting_int("news_interval_hours", 6)
        if _due(store.news_last_fetch(), hours):
            _log("开始刷新资讯")
            try:
                import feeds
                ok, failures = feeds.refresh_all()
                _state["last_news"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                _state["news_ok"] = ok
                did.append(f"刷新资讯：{ok} 个源")
                _log(f"资讯刷新完成，{ok} 个源有内容")
                if failures and ok == 0:
                    _record_error("资讯全部失败：" + "；".join(failures[:2]))
                elif failures:
                    _log("部分源失败: " + "；".join(failures[:2]))
            except Exception as exc:  # noqa: BLE001
                _record_error(f"刷新资讯出错：{type(exc).__name__}: {exc}")

    # 2. 备份：每天一次
    if _setting_bool("auto_backup", True):
        if _due(_state["last_backup"], 24):
            try:
                keep = _setting_int("backup_keep", 7)
                path = run_backup(keep=keep)
                did.append(f"备份：{os.path.basename(path)}")
                _log(f"已备份 {os.path.basename(path)}（保留 {keep} 份）")
            except Exception as exc:  # noqa: BLE001
                _record_error(f"备份出错：{type(exc).__name__}: {exc}")

    # 3. WAL 合并：每 6 小时
    if _due(_state["last_checkpoint"], 6):
        try:
            store.checkpoint()
            _state["last_checkpoint"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            _log("已合并 WAL")
        except Exception as exc:  # noqa: BLE001
            _record_error(f"合并 WAL 出错：{type(exc).__name__}: {exc}")

    return did


def _loop(stop_event):
    _state["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    _log("后台维护已启动，20 秒后做第一轮检查")
    # 启动后先等一会儿，别和正在处理的请求抢
    time.sleep(20)
    while not stop_event.is_set():
        try:
            tick()
        except Exception as exc:  # noqa: BLE001
            _record_error(f"维护循环出错：{type(exc).__name__}: {exc}")
        stop_event.wait(CHECK_INTERVAL)


def start():
    """启动后台线程。重复调用只会有一次真正生效。"""
    if _state.get("thread") and _state["thread"].is_alive():
        return
    stop_event = threading.Event()
    thread = threading.Thread(target=_loop, args=(stop_event,), daemon=True,
                              name="maintenance")
    thread.start()
    _state["thread"] = thread
    _state["stop_event"] = stop_event


if __name__ == "__main__":
    store.init()
    print("手动跑一轮维护：")
    for item in tick():
        print("  " + item)
    print("\n状态：")
    for key, value in state().items():
        if key in ("thread", "stop_event"):
            continue
        print(f"  {key:<18} {value}")
    print("\n已有备份：")
    for b in list_backups()[:5]:
        print(f"  {b['name']}  {b['size_kb']:.0f} KB  {b['mtime']}")
