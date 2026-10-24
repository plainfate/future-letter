#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取这台机器自己的状态：CPU、内存、磁盘、温度、运行时长。

只读 /proc 和 /sys，不需要 root，也不装任何包。
在非 Linux 环境（比如本地 Windows 上开发）会优雅降级成"读不到"。
"""

import os
import shutil
import time

CPU_TEMP_PATHS = [
    "/sys/class/thermal/thermal_zone0/temp",
    "/sys/class/hwmon/hwmon0/temp1_input",
]


def _read(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return default


def boot_time():
    raw = _read("/proc/stat")
    if not raw:
        return None
    for line in raw.splitlines():
        if line.startswith("btime"):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return None
    return None


def uptime_text():
    started = boot_time()
    if started:
        seconds = int(time.time()) - started
    else:
        raw = _read("/proc/uptime")
        if not raw:
            return "未知"
        seconds = int(float(raw.split()[0]))
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days} 天 {hours} 小时"
    if hours:
        return f"{hours} 小时 {minutes} 分"
    return f"{minutes} 分"


def load_avg():
    raw = _read("/proc/loadavg")
    if not raw:
        return None
    parts = raw.split()
    try:
        return [float(parts[0]), float(parts[1]), float(parts[2])]
    except (IndexError, ValueError):
        return None


def cpu_count():
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return os.cpu_count() or 1


def _meminfo():
    """一次读出 /proc/meminfo，内存和 swap 共用，别读两遍。"""
    raw = _read("/proc/meminfo")
    if not raw:
        return {}
    values = {}
    for line in raw.splitlines():
        key, _, rest = line.partition(":")
        if not rest:
            continue
        parts = rest.strip().split()
        if not parts:
            continue
        try:
            values[key] = int(parts[0])
        except ValueError:
            continue
    return values


def memory(values=None):
    """返回 (总量MB, 已用MB, 百分比) 或 None。"""
    values = values if values is not None else _meminfo()
    if not values:
        return None
    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    if not total or available is None:
        return None
    used = total - available
    return (total / 1024, used / 1024, used / total * 100)


def swap(values=None):
    values = values if values is not None else _meminfo()
    if not values:
        return None
    total = values.get("SwapTotal")
    free = values.get("SwapFree")
    if total is None or free is None:
        return None
    return (total / 1024, (total - free) / 1024)


def disk(path="/"):
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return {
        "total_gb": usage.total / 1024 ** 3,
        "used_gb": usage.used / 1024 ** 3,
        "free_gb": usage.free / 1024 ** 3,
        "percent": usage.used / usage.total * 100 if usage.total else 0,
    }


def cpu_temp():
    for path in CPU_TEMP_PATHS:
        raw = _read(path)
        if raw:
            try:
                value = int(raw)
                if value > 1000:
                    value /= 1000
                if 0 < value < 150:
                    return value
            except ValueError:
                continue
    return None


def hostname():
    raw = _read("/proc/sys/kernel/hostname")
    return raw or os.environ.get("COMPUTERNAME", "未知")


def kernel():
    raw = _read("/proc/sys/kernel/osrelease")
    return raw or "未知"


CODENAMES = ("bookworm", "trixie", "bullseye", "buster", "forky", "sid", "noble")


def os_name():
    raw = _read("/etc/os-release")
    if not raw:
        return "未知"
    name = "未知"
    for line in raw.splitlines():
        if line.startswith("PRETTY_NAME="):
            name = line.split("=", 1)[1].strip().strip('"')
            break
    # "Armbian OS 26.08.0 bookworm" -> "Armbian 26.08.0"，格子才放得下
    words = [w for w in name.split() if w not in ("OS",) + CODENAMES]
    short = " ".join(words)
    return short or name


def process_info():
    """当前进程的内存占用与线程数。"""
    pid = os.getpid()
    status = _read(f"/proc/{pid}/status")
    if not status:
        return None
    info = {}
    for line in status.splitlines():
        key, _, rest = line.partition(":")
        if key in ("VmRSS", "Threads"):
            info[key] = rest.strip()
    rss = info.get("VmRSS", "").split()
    threads = info.get("Threads", "?")
    mb = None
    if rss:
        try:
            mb = int(rss[0]) / 1024
        except ValueError:
            mb = None
    return {"rss_mb": mb, "threads": threads}


def collect(db_path=None):
    """汇总成适合直接展示的字典。"""
    meminfo = _meminfo()          # /proc/meminfo 只读一次
    mem = memory(meminfo)
    sw = swap(meminfo)
    d = disk()
    proc = process_info()
    db_size = None
    if db_path and os.path.exists(db_path):
        db_size = os.path.getsize(db_path) / 1024

    return {
        "hostname": hostname(),
        "os": os_name(),
        "kernel": kernel(),
        "uptime": uptime_text(),
        "cpus": cpu_count(),
        "load": load_avg(),
        "mem_total": mem[0] if mem else None,
        "mem_used": mem[1] if mem else None,
        "mem_percent": mem[2] if mem else None,
        "swap_total": sw[0] if sw else None,
        "swap_used": sw[1] if sw else None,
        "disk_total": d["total_gb"] if d else None,
        "disk_used": d["used_gb"] if d else None,
        "disk_free": d["free_gb"] if d else None,
        "disk_percent": d["percent"] if d else None,
        "temp": cpu_temp(),
        "proc_rss": proc["rss_mb"] if proc else None,
        "proc_threads": proc["threads"] if proc else None,
        "db_size_kb": db_size,
    }


if __name__ == "__main__":
    print("--- 本机 ---")
    for k, v in collect().items():
        print(f"  {k:<14} {v}")
