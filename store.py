#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据层。

连接按线程复用（每个请求线程一条），不再每次开关数据库 —— 这是之前
每个页面都要多花几毫秒的原因之一。WAL 模式下并发读不会互相阻塞。
"""

import os
import sqlite3
import sys
import threading
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS letters (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    body       TEXT NOT NULL,
    unlock_at  TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS days (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    title    TEXT NOT NULL,
    date     TEXT NOT NULL,
    repeat_yearly INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS since (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    title    TEXT NOT NULL,
    start_at TEXT NOT NULL,
    note     TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT NOT NULL,
    mood       TEXT NOT NULL DEFAULT '',
    body       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS news (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    feed       TEXT NOT NULL,
    title      TEXT NOT NULL,
    link       TEXT NOT NULL UNIQUE,
    summary    TEXT NOT NULL DEFAULT '',
    published  TEXT NOT NULL DEFAULT '',
    fetched_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_news_pub ON news(published DESC);
"""

_local = threading.local()


def connect():
    """取当前线程的连接（没有就建一条）。不要 close，留着复用。"""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn = conn
    return conn


def init():
    conn = connect()

    # 老版本的 notes 表给 entry_date 加了 UNIQUE，导致一天只能写一条。
    # 这里就地迁移：建新表、搬数据、换名。数据一条都不丢。
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='notes'"
    ).fetchone()
    if row and "UNIQUE" in (row["sql"] or "").upper():
        conn.executescript("""
            CREATE TABLE notes_new (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                mood       TEXT NOT NULL DEFAULT '',
                body       TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            INSERT INTO notes_new (id, entry_date, mood, body,
                                   created_at, updated_at)
                SELECT id, entry_date, mood, body, created_at, updated_at
                FROM notes;
            DROP TABLE notes;
            ALTER TABLE notes_new RENAME TO notes;
        """)
        conn.commit()
        print("已把手记表改成一天可以写多条", file=sys.stderr)

    conn.executescript(SCHEMA)
    # 课程表已经砍掉了，清掉旧版本留下的表
    conn.execute("DROP TABLE IF EXISTS courses")
    # 旧版日记表叫 diary，迁移到 notes
    has_old = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='diary'"
    ).fetchone()
    if has_old:
        conn.execute(
            "INSERT OR IGNORE INTO notes (entry_date, mood, body, created_at, updated_at) "
            "SELECT entry_date, mood, body, created_at, updated_at FROM diary"
        )
        conn.execute("DROP TABLE diary")
    # 旧版待读表叫 readlater；再早的叫 reading。功能已移除。
    for stale in ("readlater", "reading"):
        has = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (stale,)).fetchone()
        if not has:
            continue
        rows = conn.execute(f"SELECT COUNT(*) AS n FROM {stale}").fetchone()["n"]
        if rows == 0:
            conn.execute(f"DROP TABLE {stale}")
        else:
            # 有数据就不动它，宁可留着也不悄悄删
            print(f"注意：旧表 {stale} 里还有 {rows} 条记录，未删除。",
                  file=sys.stderr)
    conn.commit()


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------- 设置

def get_setting(key, default=""):
    row = connect().execute(
        "SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    conn = connect()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
    conn.commit()


def all_settings():
    rows = connect().execute("SELECT key, value FROM settings").fetchall()
    return {r["key"]: r["value"] for r in rows}


# ---------------------------------------------------------------- 信

def letters_list():
    return connect().execute(
        "SELECT id, title, unlock_at FROM letters ORDER BY unlock_at ASC"
    ).fetchall()


def letter_get(letter_id):
    return connect().execute(
        "SELECT * FROM letters WHERE id = ?", (letter_id,)).fetchone()


def letter_add(title, body, unlock_at):
    conn = connect()
    cur = conn.execute(
        "INSERT INTO letters (title, body, unlock_at, created_at) VALUES (?,?,?,?)",
        (title, body, unlock_at, now_text()))
    conn.commit()
    return cur.lastrowid


def letter_delete(letter_id):
    conn = connect()
    conn.execute("DELETE FROM letters WHERE id = ?", (letter_id,))
    conn.commit()


# ---------------------------------------------------------------- 倒数日

def days_list():
    return connect().execute("SELECT * FROM days ORDER BY date ASC").fetchall()


def day_add(title, date_text, repeat_yearly):
    conn = connect()
    cur = conn.execute(
        "INSERT INTO days (title, date, repeat_yearly, created_at) VALUES (?,?,?,?)",
        (title, date_text, 1 if repeat_yearly else 0, now_text()))
    conn.commit()
    return cur.lastrowid


def day_delete(day_id):
    conn = connect()
    conn.execute("DELETE FROM days WHERE id = ?", (day_id,))
    conn.commit()


# ---------------------------------------------------------------- 已经多久

def since_list():
    return connect().execute(
        "SELECT * FROM since ORDER BY start_at ASC").fetchall()


def since_add(title, start_at, note=""):
    conn = connect()
    cur = conn.execute(
        "INSERT INTO since (title, start_at, note, created_at) VALUES (?,?,?,?)",
        (title, start_at, note, now_text()))
    conn.commit()
    return cur.lastrowid


def since_delete(item_id):
    conn = connect()
    conn.execute("DELETE FROM since WHERE id = ?", (item_id,))
    conn.commit()


# ---------------------------------------------------------------- 手记

def notes_by_date(entry_date):
    """某一天的所有手记，按写入时间排。"""
    return connect().execute(
        "SELECT * FROM notes WHERE entry_date = ? ORDER BY id ASC",
        (entry_date,)).fetchall()


def note_get(note_id):
    return connect().execute(
        "SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()


def note_add(entry_date, mood, body):
    """新增一条手记。一天可以写多条。"""
    conn = connect()
    cur = conn.execute(
        "INSERT INTO notes (entry_date, mood, body, created_at, updated_at) "
        "VALUES (?,?,?,?,?)",
        (entry_date, mood, body, now_text(), now_text()))
    conn.commit()
    return cur.lastrowid


def note_update(note_id, mood, body):
    conn = connect()
    conn.execute(
        "UPDATE notes SET mood = ?, body = ?, updated_at = ? WHERE id = ?",
        (mood, body, now_text(), note_id))
    conn.commit()


def notes_recent(limit=100):
    """最近的手记（按日期倒序，同日按 id 倒序）。"""
    return connect().execute(
        "SELECT * FROM notes ORDER BY entry_date DESC, id DESC LIMIT ?",
        (limit,)).fetchall()


def note_delete(note_id):
    conn = connect()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()


def notes_dates():
    """有手记的日期，去重倒序。"""
    return [r["entry_date"] for r in connect().execute(
        "SELECT DISTINCT entry_date FROM notes ORDER BY entry_date DESC")]

def notes_activity(days_back=400):
    """按日期统计手记字数，给热力图用。返回 {date 对象: 字数}。"""
    from datetime import date, timedelta
    since_date = (date.today() - timedelta(days=days_back)).isoformat()
    rows = connect().execute(
        "SELECT entry_date, body FROM notes WHERE entry_date >= ?",
        (since_date,)).fetchall()
    activity = {}
    for row in rows:
        try:
            key = date.fromisoformat(row["entry_date"])
        except ValueError:
            continue
        # 按字符数算，中文一个字算一个
        activity[key] = len(row["body"] or "")
    return activity


# ---------------------------------------------------------------- 新闻

NEWS_MAX_ROWS = 400  # 再多也没人翻得到，只占地方


def news_replace(feed_name, items):
    conn = connect()
    stamp = now_text()
    for title, link, summary, published in items:
        conn.execute(
            "INSERT INTO news (feed, title, link, summary, published, fetched_at) "
            "VALUES (?,?,?,?,?,?) "
            "ON CONFLICT(link) DO UPDATE SET title = excluded.title, "
            "summary = excluded.summary, published = excluded.published, "
            "fetched_at = excluded.fetched_at",
            (feed_name, title, link, summary, published, stamp))
    # 超出上限就删最旧的，别让库无限长大
    conn.execute(
        "DELETE FROM news WHERE id NOT IN ("
        "  SELECT id FROM news ORDER BY published DESC, id DESC LIMIT ?)",
        (NEWS_MAX_ROWS,))
    conn.commit()


def news_list(limit=40):
    return connect().execute(
        "SELECT feed, title, link, summary, published FROM news "
        "ORDER BY published DESC, id DESC LIMIT ?", (limit,)).fetchall()


def news_last_fetch():
    row = connect().execute("SELECT MAX(fetched_at) AS t FROM news").fetchone()
    return row["t"] if row else None


def news_count():
    row = connect().execute("SELECT COUNT(*) AS n FROM news").fetchone()
    return row["n"] if row else 0


# ---------------------------------------------------------------- 统计

def stats():
    """各表行数，设置页用。"""
    conn = connect()
    out = {}
    for table in ("letters", "days", "notes", "news"):
        try:
            out[table] = conn.execute(
                f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        except sqlite3.Error:
            out[table] = 0
    return out


def checkpoint():
    """把 WAL 里的改动并回主库。

    开了 WAL 之后，最近的写入可能还在 data.db-wal 里；只拷 data.db
    会丢掉这些改动。备份前必须先并回去。
    """
    conn = connect()
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.commit()
        return True
    finally:
        pass


def backup_to(target_path):
    """把数据库完整复制到别处（先 checkpoint，再用 sqlite 自己的备份 API）。"""
    checkpoint()
    target = sqlite3.connect(target_path)
    try:
        connect().backup(target)
    finally:
        target.close()
    return os.path.getsize(target_path)


if __name__ == "__main__":
    init()
    print("初始化完成:", DB_PATH)
    conn = connect()
    tables = sorted(r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"))
    print("表:", ", ".join(tables))
    print("行数:", stats())
