#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RSS 抓取：只用标准库，解析 RSS 2.0 与 Atom，顺手洗掉 HTML。

抓取失败不影响网站 —— 读的是本地缓存，刷新失败只是数据旧一点。
"""

import html
import json
import re
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

import store

UA = ("Mozilla/5.0 (X11; Linux aarch64; rv:120.0) Gecko/20100101 "
      "Firefox/120.0 FutureLetter/1.0")

DEFAULT_FEEDS = [
    {"name": "36氪", "url": "https://www.36kr.com/feed"},
    {"name": "少数派", "url": "https://sspai.com/feed"},
    {"name": "Solidot", "url": "https://www.solidot.org/index.rss"},
    {"name": "IT之家", "url": "https://www.ithome.com/rss/"},
    {"name": "开源中国", "url": "https://www.oschina.net/news/rss"},
]

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean_text(raw, limit=240):
    if not raw:
        return ""
    text = TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    text = SPACE_RE.sub(" ", text).strip()
    if len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def _localname(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def _child_text(node, *names):
    for name in names:
        for child in node:
            if _localname(child.tag) == name and child.text:
                return child.text
    return ""


def _parse_date(raw):
    """把各种日期格式统一成 'YYYY-MM-DD HH:MM'，失败则原样返回。"""
    if not raw:
        return ""
    raw = raw.strip()
    candidates = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S  %z",
        "%Y-%m-%d",
    ]
    for fmt in candidates:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    # 带毫秒或奇怪时区的 ISO 字符串
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}"
    return ""


def parse_feed(raw, limit=25):
    """返回 [(title, link, summary, published)]。"""
    items = []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return items

    for node in root.iter():
        name = _localname(node.tag)
        if name not in ("item", "entry"):
            continue
        title = clean_text(_child_text(node, "title"), 160)
        link = _child_text(node, "link")
        if not link:
            # Atom: <link href="..."/>
            for child in node:
                if _localname(child.tag) == "link" and child.get("href"):
                    if child.get("rel") in (None, "alternate"):
                        link = child.get("href")
                        break
        summary = clean_text(
            _child_text(node, "description", "summary", "content"), 240
        )
        published = _parse_date(
            _child_text(node, "pubDate", "published", "updated", "date")
        )
        if title and link:
            items.append((title, link.strip(), summary, published))
        if len(items) >= limit:
            break
    return items


def fetch_one(feed, results, index):
    """抓一个源，结果写进 results[index]。不用 print —— 线程里打印会互相踩。"""
    try:
        req = urllib.request.Request(feed["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read(1_500_000)
        items = parse_feed(raw)
        results[index] = (feed["name"], items, None)
    except Exception as exc:  # noqa: BLE001 - 任何失败都只是这一源失败
        results[index] = (feed["name"], [], f"{type(exc).__name__}: {exc}"[:160])


def refresh_all(feeds=None, overall_timeout=25):
    """并发抓所有源，逐个写库。返回 (成功源数, 失败列表)。"""
    feeds = feeds if feeds is not None else load_feeds()
    if not feeds:
        return 0, []
    results = [None] * len(feeds)
    threads = []
    for i, feed in enumerate(feeds):
        t = threading.Thread(target=fetch_one, args=(feed, results, i), daemon=True)
        t.start()
        threads.append(t)

    deadline = datetime.now().timestamp() + overall_timeout
    for t in threads:
        remaining = max(0.1, deadline - datetime.now().timestamp())
        t.join(timeout=remaining)

    ok = 0
    failures = []
    for entry in results:
        if entry is None:
            failures.append("某个源超时未返回")
            continue
        name, items, error = entry
        if error:
            failures.append(f"{name}: {error}")
            continue
        if items:
            store.news_replace(name, items)
            ok += 1
        else:
            failures.append(f"{name}: 解析不到条目")
    return ok, failures


# ---------------------------------------------------------------- 源管理

def load_feeds():
    raw = store.get_setting("feeds_json", "")
    if not raw:
        return list(DEFAULT_FEEDS)
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [f for f in data if f.get("url")]
    except (ValueError, AttributeError):
        pass
    return list(DEFAULT_FEEDS)


def save_feeds(feeds):
    store.set_setting("feeds_json", json.dumps(feeds, ensure_ascii=False))


if __name__ == "__main__":
    store.init()
    ok, failures = refresh_all()
    print(f"成功 {ok} 个源")
    for f in failures:
        print("  失败:", f)
    for row in store.news_list(8):
        print(f"  [{row['feed']}] {row['title'][:40]}  {row['published']}")
