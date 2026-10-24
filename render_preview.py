#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染各页面为独立 HTML（CSS 内联进 preview，方便截图）。"""

import os
import re
import shutil
import sys
import tempfile
from datetime import date, timedelta

here = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(prefix="look3_")
for name in ("app.py", "store.py", "feeds.py", "lunar.py", "themes.py",
             "quotes.py", "sysinfo.py", "heatmap.py", "elapsed.py",
             "maintenance.py"):
    shutil.copy(os.path.join(here, name), os.path.join(tmp, name))
os.chdir(tmp)
sys.path.insert(0, tmp)

import app      # noqa: E402
import store    # noqa: E402

store.init()
app.set_password("preview")
store.set_setting("site_title", "去往未来")
theme = os.environ.get("PREVIEW_THEME", "sunrise")
store.set_setting("theme", theme)

today = date.today()


def d(days):
    return (today + timedelta(days=days)).isoformat()


store.letter_add("给三十岁的我，你好",
                 "三十岁的我，你好。\n\n我现在二十四岁，正在写这封信。\n\n"
                 "我不知道你现在过得怎么样，是不是还在坚持写东西，"
                 "是不是还住在那个城市。\n\n"
                 "如果你已经忘了今天为什么难过，那也没关系，说明它确实过去了。",
                 d(365 * 6))
store.letter_add("等孩子出生那天再打开",
                 "写给还没见面的你。\n\n妈妈现在还不知道你什么时候来。", d(200))
store.letter_add("第一份工作的最后一天",
                 "今天收拾完工位，最后一次关掉那盏灯。", d(40))
store.letter_add("写给一年后的自己",
                 "一年后再看这段话，希望你已经不再熬夜了。\n\n"
                 "希望你还记得，那时候的你以为天要塌下来了，其实没有。", d(-180))
store.letter_add("搬去新城市之前",
                 "把这张纸留在这里。\n\n如果有一天你后悔了，就回来看一眼，"
                 "当时的你是多想走。\n\n想清楚的理由，比一时的情绪更值得相信。",
                 d(-30))

store.day_add("高等数学期末考", d(12), False)
store.day_add("妈妈的生日", (today + timedelta(days=53)).isoformat(), True)
store.day_add("元旦", f"{today.year + 1}-01-01", True)
store.day_add("室友的婚礼", d(86), False)

store.since_add("搬来这座城市", "2023-06-01", "拖着两个箱子")
store.since_add("学会做饭", "2024-03-15", "第一次没把鸡蛋煎糊")
store.since_add("开始记手记", (today - timedelta(days=127)).isoformat(), "")
store.since_add("毕业", "2028-06-30", "还在倒数")

# 造一年的手记，热力图才有东西看
import random
random.seed(11)
cursor = today - timedelta(days=330)
while cursor <= today:
    if random.random() < 0.52:
        chars = random.choice([30, 60, 120, 260, 520, 1300])
        store.note_add(cursor.isoformat(),
                        random.choice(["🙂", "😊", "😐", "😴"]),
                        "今" * chars)
    cursor += timedelta(days=1)

store.note_add(today.isoformat(), "🙂",
                "今天把网站重写了一遍。印象派那套配色比之前舒服得多，"
                "像把字写在没干的画上。\n\n顺手把番茄钟和课程表砍了 —— "
                "谁会在网页里用番茄钟呢。")
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
    ("拿到2亿美金融资，Today AI 回答了 Personal AI 的十个核心问题",
     "https://36kr.com/p/1", "从工具到伙伴，个人 AI 的产品形态正在收敛。",
     "2026-10-24 18:50"),
    ("信通院报告：大模型价格回升明显，词元价格较去年下半年翻倍",
     "https://36kr.com/p/2", "量价齐升，日均消耗量增长 3 倍。",
     "2026-10-24 14:25"),
])
store.news_replace("Solidot", [
    ("Google 修改隐私条款将 Gmail 和照片数据用于个性化广告",
     "https://www.solidot.org/story?sid=1", "条款更新后，用户数据用途进一步扩大。",
     "2026-10-24 20:53"),
])

pages = {
    "home": app.view_home(),
    "letters": app.view_letters(),
    "letter": app.view_letter(2),
    "sealed": app.view_letter(1),
    "news": app.view_news(),
    "time": app.view_time(),
    "notes": app.view_notes(today.isoformat()),
    "quotes": app.view_quotes(),
    "quotes_en": app.view_quotes(0, "en"),
    "settings": app.view_settings(),
}

css = app.themes.css_for(theme)
for name, html_text in pages.items():
    # 截图用：把外链 CSS 换成就地 style，省得 file:// 去请求
    html_text = re.sub(r'<link rel="stylesheet" href="[^"]*">',
                       f"<style>{css}</style>", html_text)
    with open(f"{name}.html", "w", encoding="utf-8") as f:
        f.write(html_text)

for name in pages:
    print(os.path.join(tmp, name + ".html"))
