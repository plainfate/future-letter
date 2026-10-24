#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""热力图：把每天写了多少字画成一张像 GitHub 那样的方格图。

一年 53 列 × 7 行。颜色深浅只看当天手记的字数，
没有记录的日子是空格子 —— 一眼能看出哪段时间在写、哪段断了。

纯计算 + 拼 HTML，不依赖数据库之外的任何东西，方便单独测。
"""

from datetime import date, timedelta

# 字数 → 等级（0 无记录，1~4 由浅到深）
# 边界：1-50 级1，51-150 级2，151-400 级3，400 以上级4
THRESHOLDS = [(50, 1), (150, 2), (400, 3)]


def level_for(chars):
    if chars <= 0:
        return 0
    for limit, level in THRESHOLDS:
        if chars <= limit:
            return level
    return 4


def build(activity, weeks=53, today=None):
    """activity: {date: 字数}。返回可以直接喂给模板的结构。"""
    today = today or date.today()
    # 以周一为每周第一天，往回推满 weeks 周
    monday = today - timedelta(days=today.weekday())
    first = monday - timedelta(days=7 * (weeks - 1))

    columns = []
    month_labels = []
    cursor = first
    while cursor <= today:
        week = []
        for offset in range(7):
            day = cursor + timedelta(days=offset)
            chars = activity.get(day, 0)
            week.append({
                "date": day,
                "chars": chars,
                "level": level_for(chars),
                "future": day > today,
                "is_today": day == today,
            })
        columns.append(week)
        # 这一周里如果有某个月的 1 号，就记个月份标签
        for offset in range(7):
            day = cursor + timedelta(days=offset)
            if day.day == 1 and day <= today:
                month_labels.append((len(columns) - 1, f"{day.month}月"))
                break
        cursor += timedelta(days=7)

    return {
        "columns": columns,
        "month_labels": month_labels,
        "weeks": len(columns),
        "stats": summarize(activity, today),
    }


def summarize(activity, today=None):
    """有记录的天数、总字数、最长连续、当前连续。"""
    today = today or date.today()
    days = sorted(d for d, chars in activity.items() if chars > 0)

    total_chars = sum(activity.values())
    total_days = len(days)

    longest = 0
    run = 0
    previous = None
    for day in days:
        if previous is not None and (day - previous).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        previous = day

    # 当前连续：从今天（或昨天）往回数，中间断一天就停
    current = 0
    probe = today
    if probe not in activity or activity.get(probe, 0) <= 0:
        probe = today - timedelta(days=1)
    while activity.get(probe, 0) > 0:
        current += 1
        probe -= timedelta(days=1)

    return {
        "days": total_days,
        "chars": total_chars,
        "longest": longest,
        "current": current,
        "first": days[0] if days else None,
    }


def render(data, base_link=None):
    """把 build() 的结果渲染成 HTML。base_link 形如 '/notes?d='。"""
    if not data["columns"]:
        return ""

    # 月份标签：按列位置摆放
    labels = [""] * data["weeks"]
    for index, text in data["month_labels"]:
        if 0 <= index < data["weeks"]:
            labels[index] = text
    months_html = "".join(
        f'<span>{text}</span>' if text else "<span></span>" for text in labels
    )

    weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
    weekdays_html = "".join(
        f'<span>{name}</span>' if i % 2 == 0 else "<span></span>"
        for i, name in enumerate(weekday_names)
    )

    cols = []
    for week in data["columns"]:
        cells = []
        for cell in week:
            if cell["future"]:
                cells.append('<i class="l0 future"></i>')
                continue
            day = cell["date"]
            if cell["chars"]:
                tip = f'{day.isoformat()} · {cell["chars"]} 字'
            else:
                tip = f'{day.isoformat()} · 没有记录'
            cls = f'l{cell["level"]}'
            if cell["is_today"]:
                cls += " today"
            if base_link:
                cells.append(
                    f'<a class="{cls}" href="{base_link}{day.isoformat()}" '
                    f'title="{tip}" aria-label="{tip}"></a>')
            else:
                cells.append(f'<i class="{cls}" title="{tip}"></i>')
        cols.append('<div class="heat-col">' + "".join(cells) + "</div>")

    stats = data["stats"]
    streak = stats["current"]
    if streak:
        streak_text = f"连着写了 {streak} 天"
    elif stats["days"]:
        streak_text = "今天还没写"
    else:
        streak_text = "还没有记录"

    return f"""
<div class="heat">
  <div class="heat-head">
    <span class="heat-stat">{streak_text}</span>
    <span class="heat-stat">{stats["days"]} 天有记录 · 共 {stats["chars"]} 字</span>
    <span class="heat-stat">最长连续 {stats["longest"]} 天</span>
  </div>
  <div class="heat-scroll">
    <div class="heat-months">{months_html}</div>
    <div class="heat-main">
      <div class="heat-weekdays">{weekdays_html}</div>
      <div class="heat-cols">{"".join(cols)}</div>
    </div>
  </div>
  <div class="heat-legend">
    <span>少</span><i class="l0"></i><i class="l1"></i><i class="l2"></i>
    <i class="l3"></i><i class="l4"></i><span>多</span>
  </div>
</div>"""


if __name__ == "__main__":
    from datetime import date as d

    today = d(2026, 10, 24)
    sample = {}
    # 造一年的样例数据
    day = today - timedelta(days=300)
    import random
    random.seed(7)
    while day <= today:
        if random.random() < 0.45:
            sample[day] = random.choice([20, 80, 200, 600, 1200])
        day += timedelta(days=1)

    data = build(sample, today=today)
    s = data["stats"]
    print(f"列数 {data['weeks']}  月份标签 {len(data['month_labels'])}")
    print(f"有记录 {s['days']} 天 / 共 {s['chars']} 字 / "
          f"最长连续 {s['longest']} 天 / 当前 {s['current']} 天")
    html = render(data, "/notes?d=")
    print(f"HTML {len(html)} 字符")
    assert 'class="l4"' in html or 'class="l3"' in html
    assert "连着写了" in html
    print("自检通过")
