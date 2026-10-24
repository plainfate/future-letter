#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把页面放进固定宽度的 iframe 里截图，确保媒体查询真的按手机宽度生效。

Edge 的旧版无头模式不认 --window-size，直接截会按更宽的视口渲染再裁掉右边，
看起来像"内容溢出"，其实是截图工具的假象。用 iframe 就准确了。
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, timedelta

here = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(prefix="mob_")
for m in ("app.py", "store.py", "feeds.py", "lunar.py", "themes.py",
          "quotes.py", "sysinfo.py"):
    shutil.copy(os.path.join(here, m), os.path.join(tmp, m))
os.chdir(tmp)
sys.path.insert(0, tmp)

import app      # noqa: E402
import store    # noqa: E402

store.init()
app.set_password("preview")
store.set_setting("site_title", "去往未来")
store.set_setting("theme", os.environ.get("PREVIEW_THEME", "impression"))

today = date.today()


def d(days):
    return (today + timedelta(days=days)).isoformat()


store.letter_add("给三十岁的我，你好",
                 "三十岁的我，你好。\n\n我现在二十四岁，正在写这封信。\n\n"
                 "我不知道你现在过得怎么样，是不是还在坚持写东西。", d(365 * 6))
store.letter_add("等孩子出生那天再打开", "写给还没见面的你。", d(200))
store.letter_add("第一份工作的最后一天", "今天收拾完工位。", d(40))
store.letter_add("写给一年后的自己",
                 "一年后再看这段话，希望你已经不再熬夜了。", d(-180))
store.letter_add("搬去新城市之前", "想清楚的理由，比一时的情绪更值得相信。", d(-30))

store.day_add("高等数学期末考", d(12), False)
store.day_add("妈妈的生日", (today + timedelta(days=53)).isoformat(), True)
store.day_add("元旦", f"{today.year + 1}-01-01", True)
store.day_add("室友的婚礼", d(86), False)

store.note_add(today.isoformat(), "🙂",
                "今天把网站重写了一遍，砍掉了番茄钟和课程表。"
                "顺手修了手机上配色错乱的问题。")
store.note_add((today - timedelta(days=365)).isoformat(), "😊",
                "一年前的今天，还在为同一件事发愁。现在回头看，其实没什么。")
store.note_add((today - timedelta(days=3)).isoformat(), "😴",
                "什么都没干成的一天，但睡够了。")

store.news_replace("少数派", [
    ("在硅谷，遇见个人计算机历史", "https://sspai.com/post/116128",
     "从车库到展厅，一段被反复讲述的历史。", "2026-10-24 16:26"),
    ("本周看什么：最近值得一看的 12 部作品", "https://sspai.com/post/117169",
     "电影、剧集、书籍，编辑部的一周清单。", "2026-10-23 18:09"),
])
store.news_replace("36氪", [
    ("信通院报告：大模型价格回升明显", "https://36kr.com/p/2",
     "量价齐升，日均消耗量增长 3 倍。", "2026-10-24 14:25"),
])

css = app.themes.css_for(app.current_theme())

pages = {
    "home": app.view_home(),
    "letters": app.view_letters(),
    "notes": app.view_notes(today.isoformat()),
    "quotes": app.view_quotes(),
    "settings": app.view_settings(),
    "news": app.view_news(),
}

WIDTHS = {"m": 390, "s": 360}
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
shots_dir = os.path.join(here, "shots")

for name, html in pages.items():
    html = re.sub(r'<link rel="stylesheet" href="[^"]*">',
                  f"<style>{css}</style>", html)
    inner_path = os.path.join(tmp, f"{name}.html")
    with open(inner_path, "w", encoding="utf-8") as f:
        f.write(html)

    for prefix, width in WIDTHS.items():
        host = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>body{{margin:0;background:#fff}}
iframe{{width:{width}px;height:1600px;border:0;display:block}}</style>
</head><body>
<iframe src="{name}.html"></iframe>
</body></html>"""
        host_path = os.path.join(tmp, f"host_{prefix}_{name}.html")
        with open(host_path, "w", encoding="utf-8") as f:
            f.write(host)
        out_png = os.path.join(shots_dir, f"{prefix}_{name}.png")
        subprocess.run(
            [edge, "--headless", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1", "--window-size=420,1600",
             "--virtual-time-budget=4000", f"--screenshot={out_png}",
             f"file:///{host_path.replace(chr(92), '/')}"],
            capture_output=True, timeout=120)
        print(f"  {prefix}_{name}.png  ({width}px 宽)")

shutil.rmtree(tmp, ignore_errors=True)
print("完成")
