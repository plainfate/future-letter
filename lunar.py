#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""农历、干支、生肖与节日推算（纯标准库，1900-2100）。

只做一件事：给定公历日期，算出农历日期、干支生肖，以及离下一个重要节日还有几天。
节假日只算"传统的和固定的"（春节、端午、中秋、元旦、劳动节、国庆…），
不含调休安排 —— 调休每年由国务院公布，硬编码会算错。
"""

from datetime import date, timedelta
from functools import lru_cache

# 1900-2100 年农历数据。每个整数记录：闰月（低 4 位）、各月大小（次 12 位）、闰月大小（第 17 位）
LUNAR_INFO = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,
    0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,
    0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,
    0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,
    0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,
    0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5b0, 0x14573, 0x052b0, 0x0a9a8, 0x0e950, 0x06aa0,
    0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,
    0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b6a0, 0x195a6,
    0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,
    0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x05ac0, 0x0ab60, 0x096d5, 0x092e0,
    0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,
    0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,
    0x05aa0, 0x076a3, 0x096d0, 0x04afb, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,
    0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,
    0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06b20, 0x1a6c4, 0x0aae0,
    0x092e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0, 0x0a6d0, 0x055d4,
    0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,
    0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x04b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160,
    0x0e968, 0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,
    0x0d520,
]

BASE_DATE = date(1900, 1, 31)  # 1900 年农历正月初一

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
ZODIAC = "鼠牛虎兔龙蛇马羊猴鸡狗猪"
CN_MONTH = ["正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]
CN_DIGIT = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
CN_WEEKDAY = ["一", "二", "三", "四", "五", "六", "日"]


def leap_month(year):
    """该农历年的闰月，0 表示无闰月。"""
    return LUNAR_INFO[year - 1900] & 0xF


def leap_days(year):
    if leap_month(year):
        return 30 if LUNAR_INFO[year - 1900] & 0x10000 else 29
    return 0


def month_days(year, month):
    return 30 if LUNAR_INFO[year - 1900] & (0x10000 >> month) else 29


def year_days(year):
    total = sum(month_days(year, m) for m in range(1, 13))
    return total + leap_days(year)


# ---------------------------------------------------------------- 缓存
# solar_to_lunar 原本每次都从 1900 年逐年累加，单次就要 3 毫秒；
# 节日推算要它算上千次，页面因此要等好几秒。这里把"每年正月初一是哪天"
# 和"每年有多少天"一次算好，之后查表就是 O(1)。
_YEAR_START = None      # {农历年: 该年正月初一的公历序数}
_YEAR_SPAN = None       # {农历年: 该年天数}


def _build_cache():
    global _YEAR_START, _YEAR_SPAN
    if _YEAR_START is not None:
        return
    starts = {}
    spans = {}
    cursor = BASE_DATE.toordinal()
    for year in range(1900, 2101):
        spans[year] = year_days(year)
        starts[year] = cursor
        cursor += spans[year]
    _YEAR_START = starts
    _YEAR_SPAN = spans


def solar_to_lunar(target):
    """公历 date -> (农历年, 月, 日, 是否闰月)。超出 1900-2100 返回 None。"""
    if not (date(1900, 1, 31) <= target <= date(2100, 12, 31)):
        return None
    _build_cache()
    ordinal = target.toordinal()

    # 二分查找落在哪个农历年里
    lo, hi = 1900, 2100
    year = 1900
    while lo <= hi:
        mid = (lo + hi) // 2
        if _YEAR_START[mid] <= ordinal:
            year = mid
            lo = mid + 1
        else:
            hi = mid - 1

    offset = ordinal - _YEAR_START[year]
    leap = leap_month(year)
    month = 1
    while month <= 12:
        days = month_days(year, month)
        if offset < days:
            return year, month, offset + 1, False
        offset -= days
        if month == leap:
            days = leap_days(year)
            if offset < days:
                return year, month, offset + 1, True
            offset -= days
        month += 1
    return None


def ganzhi_year(lunar_year):
    """干支纪年。1900 年为庚子年。"""
    idx = (lunar_year - 1900 + 36) % 60
    return GAN[idx % 10] + ZHI[idx % 12]


def zodiac(lunar_year):
    return ZODIAC[(lunar_year - 1900 + 36) % 12]


def lunar_day_text(day):
    if day == 10:
        return "初十"
    if day == 20:
        return "二十"
    if day == 30:
        return "三十"
    tens, ones = divmod(day, 10)
    prefix = ["初", "十", "廿", "三"][tens]
    return prefix + CN_DIGIT[ones - 1]


def lunar_month_text(month, is_leap):
    return ("闰" if is_leap else "") + CN_MONTH[month - 1] + "月"


def lunar_text(target):
    """'农历丙午年 九月十五' 这样的完整描述。"""
    info = solar_to_lunar(target)
    if info is None:
        return ""
    year, month, day, is_leap = info
    return f"农历{ganzhi_year(year)}年 {lunar_month_text(month, is_leap)}{lunar_day_text(day)}"


def qingming_day(year):
    """清明（21 世纪经验公式，误差极小）。"""
    y = year % 100
    c = 4.81 if year >= 2000 else 5.59
    return int(y * 0.2422 + c) - int(y / 4)


def _nth_weekday(year, month, weekday, n):
    """某月第 n 个某星期几（weekday: 0=周一, 6=周日）。"""
    first = date(year, month, 1)
    delta = (weekday - first.weekday()) % 7
    return first + timedelta(days=delta + 7 * (n - 1))


@lru_cache(maxsize=32)
def festivals_in_year(year):
    """返回 [(date, 名称)]，含农历节日与固定公历节日。纯函数，按年缓存。"""
    out = []

    def lunar_date(month, day):
        """在该公历年里找农历某月某日对应的公历日期（取该年正月初一之后的那次）。"""
        start = date(year, 1, 1)
        for offset in range(0, 400):
            d = start + timedelta(days=offset)
            info = solar_to_lunar(d)
            if info and info[0] == year and info[1] == month and info[2] == day and not info[3]:
                return d
        return None

    lunar_festivals = [
        (1, 1, "春节"),
        (1, 15, "元宵节"),
        (5, 5, "端午节"),
        (7, 7, "七夕"),
        (8, 15, "中秋节"),
        (9, 9, "重阳节"),
        (12, 8, "腊八节"),
    ]
    for month, day, name in lunar_festivals:
        d = lunar_date(month, day)
        if d:
            out.append((d, name))

    fixed = [
        ((1, 1), "元旦"),
        ((2, 14), "情人节"),
        ((3, 8), "妇女节"),
        ((5, 1), "劳动节"),
        ((5, 4), "青年节"),
        ((6, 1), "儿童节"),
        ((9, 10), "教师节"),
        ((10, 1), "国庆节"),
        ((12, 25), "圣诞节"),
    ]
    for (m, d), name in fixed:
        out.append((date(year, m, d), name))

    # 母亲节（5 月第二个周日）、父亲节（6 月第三个周日）
    out.append((_nth_weekday(year, 5, 6, 2), "母亲节"))
    out.append((_nth_weekday(year, 6, 6, 3), "父亲节"))
    out.append((date(year, 4, qingming_day(year)), "清明"))

    return sorted(out)


def next_festivals(today, limit=4):
    """从 today 起接下来的节日，返回 [(相距天数, date, 名称)]。"""
    items = festivals_in_year(today.year) + festivals_in_year(today.year + 1)
    upcoming = [(d - today).days for d, _ in items if d >= today]
    upcoming.sort()
    result = []
    for d, name in items:
        delta = (d - today).days
        if delta >= 0:
            result.append((delta, d, name))
    result.sort(key=lambda x: (x[0], x[2]))
    return result[:limit]


def describe_today(today):
    """首页顶部那一行：公历、星期、农历、节日。"""
    info = solar_to_lunar(today)
    weekday = "星期" + CN_WEEKDAY[today.weekday()]
    parts = [f"{today.year} 年 {today.month} 月 {today.day} 日", weekday]
    if info:
        year, month, day, is_leap = info
        parts.append(f"{ganzhi_year(year)}年 · {zodiac(year)}年")
        parts.append(f"{lunar_month_text(month, is_leap)}{lunar_day_text(day)}")
    today_names = [name for d, name in festivals_in_year(today.year) if d == today]
    return {"date": today, "weekday": weekday, "lunar": lunar_text(today),
            "today_festivals": today_names, "parts": parts}


if __name__ == "__main__":
    # 自检：几个已知的春节与中秋
    EXPECTED_CNY = {2024: (2, 10), 2025: (1, 29), 2026: (2, 17), 2027: (2, 6)}
    failed = 0
    for year, (m, d) in EXPECTED_CNY.items():
        got = solar_to_lunar(date(year, m, d))
        ok = got == (year, 1, 1, False) or (got and got[0] == year and got[1] == 1 and got[2] == 1)
        print(f"  {'PASS' if ok else 'FAIL'}  {year} 春节 {m:02d}-{d:02d} -> {got}")
        failed += 0 if ok else 1

    # 中秋 2026-09-25 应为八月十五
    got = solar_to_lunar(date(2026, 9, 25))
    ok = got and got[1] == 8 and got[2] == 15
    print(f"  {'PASS' if ok else 'FAIL'}  2026 中秋 09-25 -> {got}")
    failed += 0 if ok else 1

    print("  今天:", describe_today(date.today()))
    for delta, d, name in next_festivals(date.today(), 4):
        print(f"   {name}: {d} (还有 {delta} 天)")
    print("FAILED" if failed else "ALL PASSED")
