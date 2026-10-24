#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「已经多久了」：从一个日子算到现在过了多长时间。

比单纯算天数有意思的地方：
  · 拆成 X 年 Y 个月 Z 天（按日历算，不是除以 365）；
  · 顺带算出已经过了多少小时、多少分钟；
  · 告诉你下一个整数里程碑还有多久（1000 天、10000 小时这种）；
  · 也支持倒数：离某个未来日子还有多久。
"""

from datetime import date, datetime, timedelta

# 里程碑：天数和小时数的整数关口
DAY_MILESTONES = [100, 500, 1000, 2000, 3000, 5000, 7300, 10000,
                  15000, 20000, 25000, 30000]
HOUR_MILESTONES = [1000, 5000, 10000, 20000, 50000, 100000, 200000]


def _add_months(year, month, delta):
    total = (year * 12 + (month - 1)) + delta
    return total // 12, total % 12 + 1


def _days_in_month(year, month):
    this_month = date(year, month, 1)
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    return (nxt - this_month).days


def _add_months_clamped(day, months):
    """在 day 上加 months 个月。目标月没有这一天时取月末（2/29 → 2/28）。"""
    year, month = _add_months(day.year, day.month, months)
    last = _days_in_month(year, month)
    return date(year, month, min(day.day, last))


def calendar_span(start, end):
    """按日历算 start 到 end 相差几年几个月零几天。

    做法：先找最大的整月数，使 start 加上这些月仍不超过 end；
    剩下的零头就是天数。这样闰年、月末都能自然处理。
    """
    sign = 1
    if end < start:
        start, end = end, start
        sign = -1

    months = (end.year - start.year) * 12 + (end.month - start.month)
    if months < 0:
        months = 0
    # 加多了就往回收一格
    while months > 0 and _add_months_clamped(start, months) > end:
        months -= 1
    while _add_months_clamped(start, months + 1) <= end:
        months += 1

    anchor = _add_months_clamped(start, months)
    days = (end - anchor).days
    years, remainder_months = divmod(months, 12)

    return sign * years, sign * remainder_months, sign * days


def span_text(years, months, days):
    """'3 年 2 个月 5 天' 这种，零头省略。"""
    parts = []
    if years:
        parts.append(f"{abs(years)} 年")
    if months:
        parts.append(f"{abs(months)} 个月")
    if days or not parts:
        parts.append(f"{abs(days)} 天")
    return " ".join(parts)


def next_milestone(days, milestones=None):
    """下一个整数天里程碑：返回 (天数, 还差几天) 或 None。"""
    milestones = milestones or DAY_MILESTONES
    for target in milestones:
        if target > days:
            return target, target - days
    return None


def next_hour_milestone(hours):
    for target in HOUR_MILESTONES:
        if target > hours:
            return target, target - hours
    return None


def describe(start, now=None, unit_hint="days"):
    """核心：给一个起始日子，返回一个可以直接拿去展示的字典。"""
    if now is None:
        now = datetime.now()
    if isinstance(now, datetime):
        now_date = now.date()
        now_hour = now.hour
    elif isinstance(now, date):
        now_date = now
        now_hour = 0
    else:
        raise TypeError("now 必须是 date 或 datetime")

    sign = 1 if now_date >= start else -1

    total_days = (now_date - start).days
    years, months, days = calendar_span(start, now_date)

    total_hours = total_days * 24 + now_hour
    total_minutes = total_hours * 60

    forward = sign > 0
    result = {
        "start": start,
        "days": abs(total_days),
        "hours": abs(total_hours),
        "minutes": abs(total_minutes),
        "years": abs(years),
        "months": abs(months),
        "days_remainder": abs(days),
        "span": span_text(years, months, days),
        "forward": forward,          # True = 已经过去；False = 还在倒数
        "total_days_signed": sign * total_days,
    }

    if forward:
        mg = next_milestone(abs(total_days))
        result["next_milestone"] = mg[0] if mg else None
        result["milestone_left"] = mg[1] if mg else None
        hg = next_hour_milestone(abs(total_hours))
        result["next_hour_milestone"] = hg[0] if hg else None
        result["hour_milestone_left"] = hg[1] if hg else None
        # 今天是不是整周年
        result["is_anniversary"] = (months == 0 and days == 0 and years > 0)
        # 十万小时之类的特殊点
        result["is_day_milestone"] = abs(total_days) in DAY_MILESTONES
    else:
        mg = next_milestone(abs(total_days))
        result["next_milestone"] = None
        result["milestone_left"] = None
        result["next_hour_milestone"] = None
        result["hour_milestone_left"] = None
        result["is_anniversary"] = False
        result["is_day_milestone"] = False

    return result


def summary_line(info):
    """一行摘要，用在倒数页的卡片上。"""
    if info["forward"]:
        head = f'已经 {info["span"]}'
        if info["days"] == 0:
            head = "就是今天开始的"
        tail = f'共 {info["days"]} 天'
    else:
        head = f'还有 {info["span"]}'
        tail = f'还有 {info["days"]} 天'
    return head, tail


if __name__ == "__main__":
    # 自检：用已知日期验证日历拆分
    cases = [
        # (起点, 现在, 期望的年月日)
        (date(2020, 1, 1), date(2023, 3, 15), (3, 2, 14)),
        (date(2024, 2, 29), date(2025, 3, 1), (1, 0, 1)),
        (date(2026, 1, 1), date(2026, 1, 1), (0, 0, 0)),
        (date(2025, 12, 31), date(2026, 1, 1), (0, 0, 1)),
        (date(2026, 10, 1), date(2026, 10, 24), (0, 0, 23)),
    ]
    failed = 0
    for start, now, expect in cases:
        got = calendar_span(start, now)
        ok = got == expect
        print(f"  {'PASS' if ok else 'FAIL'}  {start} → {now}: "
              f"得到 {got}，期望 {expect}")
        failed += 0 if ok else 1

    print()
    demo_start = date(2023, 6, 1)
    info = describe(demo_start, datetime(2026, 10, 24, 15, 30))
    print(f"从 {demo_start} 到现在：")
    print(f"  {info['span']}（共 {info['days']} 天 / {info['hours']} 小时）")
    print(f"  下一个里程碑：{info['next_milestone']} 天，"
          f"还差 {info['milestone_left']} 天")
    print(f"  下一个小时里程碑：{info['next_hour_milestone']} 小时，"
          f"还差 {info['hour_milestone_left']} 小时")

    future = date(2027, 1, 1)
    info2 = describe(future, datetime(2026, 10, 24, 15, 30))
    print(f"\n离 {future}：{info2['span']}（还有 {info2['days']} 天）")
    print("FAILED" if failed else "ALL PASSED")
