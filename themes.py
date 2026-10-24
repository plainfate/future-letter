#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主题：印象派水彩（默认）、纸上书信、深夜台灯。

移动端要点（都是踩过的坑）：
  · 不用 background-attachment:fixed（iOS Safari 会让渐变错位/变纯色），
    改成 position:fixed 的伪元素垫在最底层；
  · 输入框字号至少 16px，否则 iOS 聚焦时会自动放大且不还原；
  · 导航可横向滑动，链接点击区不小于 44px；
  · 主题选中态用 :has() 表达，不依赖 JS 切 class。
"""

import functools

THEMES = {
    "impression": {
        "name": "印象派 · 水彩",
        "desc": "莫奈睡莲：米白纸底，淡紫雾蓝的晕染。",
        "vars": {
            "bg": "#f2efe6",
            "wash1": "rgba(168,158,214,0.42)",
            "wash2": "rgba(146,180,200,0.36)",
            "wash3": "rgba(214,166,168,0.30)",
            "wash4": "rgba(176,196,160,0.28)",
            "card": "rgba(255,253,247,0.72)",
            "card_hover": "rgba(255,254,250,0.94)",
            "ink": "#3b3a4a",
            "ink_soft": "#6b6879",
            "ink_faint": "#98939f",
            "line": "rgba(107,104,121,0.20)",
            "accent": "#8d7fb8",
            "accent_ink": "#5c4f84",
            "sealed_bg": "rgba(255,252,245,0.66)",
            "shadow": "0 4px 22px rgba(107,104,121,0.10)",
            "shadow_hover": "0 8px 30px rgba(107,104,121,0.17)",
        },
        "font": ('"Songti SC","Source Han Serif SC","Noto Serif CJK SC",'
                 '"Noto Serif SC","STSong","SimSun",Georgia,serif'),
    },
    "paper": {
        "name": "纸上书信",
        "desc": "暖白信纸，墨黑宋体，一点朱砂红。",
        "vars": {
            "bg": "#faf6ef",
            "wash1": "rgba(214,196,168,0.22)",
            "wash2": "rgba(200,188,170,0.16)",
            "wash3": "rgba(214,176,160,0.14)",
            "wash4": "rgba(190,196,174,0.12)",
            "card": "rgba(255,255,255,0.78)",
            "card_hover": "rgba(255,255,255,0.96)",
            "ink": "#2e2a25",
            "ink_soft": "#6a625a",
            "ink_faint": "#9c948a",
            "line": "rgba(106,98,90,0.22)",
            "accent": "#b5462f",
            "accent_ink": "#8c3323",
            "sealed_bg": "rgba(255,255,255,0.7)",
            "shadow": "0 2px 14px rgba(74,64,52,0.08)",
            "shadow_hover": "0 6px 24px rgba(74,64,52,0.14)",
        },
        "font": ('"Songti SC","Source Han Serif SC","Noto Serif CJK SC",'
                 '"Noto Serif SC","STSong","SimSun",Georgia,serif'),
    },
    "night": {
        "name": "深夜台灯",
        "desc": "深蓝黑底，暖白字，不用金色。",
        "vars": {
            "bg": "#171b26",
            "wash1": "rgba(94,110,168,0.30)",
            "wash2": "rgba(70,96,130,0.26)",
            "wash3": "rgba(150,110,130,0.18)",
            "wash4": "rgba(80,120,110,0.18)",
            "card": "rgba(38,44,58,0.72)",
            "card_hover": "rgba(48,55,72,0.92)",
            "ink": "#e8e4dc",
            "ink_soft": "#a8a49c",
            "ink_faint": "#78766f",
            "line": "rgba(180,180,175,0.16)",
            "accent": "#7f93c9",
            "accent_ink": "#a3b4e0",
            "sealed_bg": "rgba(34,40,54,0.8)",
            "shadow": "0 4px 22px rgba(0,0,0,0.28)",
            "shadow_hover": "0 8px 30px rgba(0,0,0,0.42)",
        },
        "font": ('"Songti SC","Source Han Serif SC","Noto Serif CJK SC",'
                 '"Noto Serif SC","STSong","SimSun",Georgia,serif'),
    },
}

DEFAULT_THEME = "oil"

# 主题除变量外还可以带一个 body 类名，用来写该主题专属的版式
THEMES["oil"] = {
    "name": "油画 · 色块",
    "desc": "厚涂色块堆叠：墨绿、赭石、靛蓝、奶油，边是硬的。",
    "body_class": "oil",
    "vars": {
        "bg": "#e8e0cf",
        "wash1": "rgba(38,74,68,0.55)",
        "wash2": "rgba(176,92,52,0.42)",
        "wash3": "rgba(52,68,110,0.38)",
        "wash4": "rgba(198,164,82,0.40)",
        "card": "#f2ead9",
        "card_hover": "#fbf5e6",
        "ink": "#23201b",
        "ink_soft": "#544c40",
        "ink_faint": "#867a68",
        "line": "rgba(35,32,27,0.34)",
        "accent": "#1f4a44",
        "accent_ink": "#173a35",
        "sealed_bg": "#efe6d2",
        "shadow": "5px 5px 0 rgba(35,32,27,0.20)",
        "shadow_hover": "7px 7px 0 rgba(35,32,27,0.28)",
    },
    "font": ('"Songti SC","Source Han Serif SC","Noto Serif CJK SC",'
             '"Noto Serif SC","STSong","SimSun",Georgia,serif'),
}

DEFAULT_THEME = "sunrise"

# 日出：莫奈《印象·日出》—— 冷灰蓝的雾港，一轮橘红，水面一道倒影
THEMES["sunrise"] = {
    "name": "日出",
    "desc": "莫奈那幅：灰蓝的雾、一轮橘红，下面一道倒影。",
    "body_class": "sunrise",
    "vars": {
        "bg": "#dde3e2",
        "wash1": "rgba(120,140,158,0.50)",
        "wash2": "rgba(102,124,142,0.42)",
        "wash3": "rgba(96,118,132,0.34)",
        "wash4": "rgba(226,110,50,0.30)",
        "card": "rgba(250,249,244,0.80)",
        "card_hover": "rgba(253,252,248,0.97)",
        "ink": "#39464f",
        "ink_soft": "#5f6e78",
        "ink_faint": "#8b979d",
        "line": "rgba(92,110,124,0.26)",
        "accent": "#c2571f",
        "accent_ink": "#96441a",
        "sealed_bg": "rgba(248,247,242,0.74)",
        "shadow": "0 4px 22px rgba(92,110,124,0.14)",
        "shadow_hover": "0 8px 30px rgba(92,110,124,0.22)",
    },
    "font": ('"Songti SC","Source Han Serif SC","Noto Serif CJK SC",'
             '"Noto Serif SC","STSong","SimSun",Georgia,serif'),
}

FONTS = {
    "pixel": {
        "name": "像素",
        "desc": "点阵屏的感觉。装了 Zpix / 缝合像素 / 方舟像素就自动用上。",
        "stack": ('"Zpix","Fusion Pixel 12px monospaced zh_hans",'
                  '"Fusion Pixel","Ark Pixel 12px zh_hans","Ark Pixel",'
                  '"Pixelify Sans","MS Gothic","SimSun",'
                  '"Noto Sans Mono CJK SC",ui-monospace,Menlo,Consolas,'
                  'monospace'),
        "extra": "letter-spacing:.03em;font-variant-ligatures:none",
    },
    "serif": {
        "name": "宋体",
        "desc": "衬线，像纸上的活字。",
        "stack": ('"Songti SC","Source Han Serif SC","Noto Serif CJK SC",'
                  '"Noto Serif SC","STSong","SimSun",Georgia,serif'),
        "extra": "",
    },
    "sans": {
        "name": "黑体",
        "desc": "无衬线，屏幕阅读最稳。",
        "stack": ('-apple-system,"Segoe UI","PingFang SC",'
                  '"Microsoft YaHei","Noto Sans CJK SC","Source Han Sans SC",'
                  'sans-serif'),
        "extra": "",
    },
}

DEFAULT_FONT = "serif"

BASE_CSS = """
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;color:var(--ink);font:16px/1.78 var(--font);
  background-color:var(--bg);position:relative}
/* 水彩晕染垫在最底层。用 fixed 定位的伪元素承载，而不是把背景挂在 body 上
   再做 fixed 固定 —— 那种写法在 iOS Safari 上会让渐变错位或变成纯色。 */
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
  background-image:
    radial-gradient(ellipse 70% 55% at 8% 4%,var(--wash1) 0,transparent 62%),
    radial-gradient(ellipse 60% 48% at 94% 12%,var(--wash2) 0,transparent 60%),
    radial-gradient(ellipse 64% 52% at 22% 92%,var(--wash3) 0,transparent 64%),
    radial-gradient(ellipse 56% 46% at 86% 88%,var(--wash4) 0,transparent 62%)}
.wrap{max-width:820px;margin:0 auto;padding:24px 18px 60px}

header{display:flex;justify-content:space-between;align-items:baseline;gap:12px;
  flex-wrap:wrap;padding-bottom:12px;margin-bottom:20px;
  border-bottom:1px solid var(--line)}
h1.brand{font-size:19px;margin:0;letter-spacing:.14em;font-weight:600}
h1.brand a{color:var(--ink);text-decoration:none}
/* 导航：手机上可横向滑动，不换行挤压；点击区 ≥44px 高 */
nav.main{display:flex;gap:2px;overflow-x:auto;-webkit-overflow-scrolling:touch;
  scrollbar-width:none;max-width:100%}
nav.main::-webkit-scrollbar{display:none}
nav.main a{flex:0 0 auto;color:var(--ink-soft);text-decoration:none;
  font-size:13.5px;letter-spacing:.04em;padding:11px 9px;border-radius:8px;
  min-height:44px;display:flex;align-items:center;
  transition:color .15s,background .15s}
nav.main a:hover,nav.main a.on{color:var(--accent-ink);background:var(--card)}

.dateline{display:flex;flex-wrap:wrap;gap:5px 13px;align-items:baseline;
  color:var(--ink-soft);font-size:13px;letter-spacing:.03em;margin:-4px 0 20px;
  padding:10px 14px;border-radius:11px;background:var(--card);
  border:1px solid var(--line)}
.dateline b{color:var(--ink);font-size:14px;font-weight:600}
.dateline .fest{color:var(--accent-ink);font-weight:600}

.card{display:block;padding:16px 18px;margin-bottom:11px;border-radius:13px;
  background:var(--card);border:1px solid var(--line);box-shadow:var(--shadow);
  text-decoration:none;color:inherit;
  transition:transform .18s,box-shadow .18s,background .18s,border-color .18s}
a.card:hover{background:var(--card-hover);box-shadow:var(--shadow-hover);
  transform:translateY(-2px);border-color:var(--accent)}
.card h2{margin:0 0 5px;font-size:17.5px;font-weight:600;line-height:1.55}
.card h3{margin:0 0 4px;font-size:15px;font-weight:600;line-height:1.5}
.meta{color:var(--ink-faint);font-size:12.5px;letter-spacing:.03em}
.locked{border-style:dashed;box-shadow:none;opacity:.88}
.locked h2::after{content:" · 未解锁";font-size:11.5px;font-weight:400;
  color:var(--ink-faint);letter-spacing:.06em}
.locked .cd{color:var(--accent-ink);font-size:12.5px;margin-top:2px}

.sealed{padding:44px 22px;text-align:center;border-radius:16px;
  background:var(--sealed-bg);border:1px dashed var(--line);box-shadow:var(--shadow)}
.sealed .mark{font-size:30px;line-height:1;margin-bottom:16px;opacity:.7}
.sealed h2{font-size:19.5px;margin:0 0 9px;font-weight:600}
.sealed .cd{color:var(--accent-ink);font-size:14px;margin-top:16px;
  letter-spacing:.08em}

article .letter{font-size:17px;line-height:2.1;white-space:pre-wrap;
  word-wrap:break-word;overflow-wrap:anywhere;padding:4px 0 22px}
h2.page{font-size:19.5px;margin:0 0 6px;font-weight:600;letter-spacing:.03em}
h2.page.sub{margin-top:30px}
p.lead{color:var(--ink-soft);font-size:13.5px;margin:0 0 6px}
hr.thin{border:0;border-top:1px solid var(--line);margin:16px 0 6px}

label{display:block;font-size:12.5px;color:var(--ink-soft);margin:18px 0 6px;
  letter-spacing:.04em}
/* 16px 是硬要求：小于它 iOS 聚焦时会自动放大页面且不还原 */
input,textarea,select{width:100%;padding:11px 12px;border-radius:10px;
  border:1px solid var(--line);background:var(--card);color:var(--ink);
  font-family:inherit;font-size:16px;line-height:1.5;
  transition:border-color .16s,background .16s}
input:focus,textarea:focus,select:focus{outline:none;border-color:var(--accent);
  background:var(--card-hover)}
input[type=checkbox]{width:auto;min-height:0;margin:0}
textarea{min-height:170px;resize:vertical;line-height:1.85}
textarea.tall{min-height:280px}
button{margin-top:18px;padding:12px 24px;border-radius:10px;border:0;
  background:var(--accent);color:#fff;font-family:inherit;font-size:16px;
  font-weight:600;cursor:pointer;letter-spacing:.06em;min-height:44px;
  transition:filter .16s,transform .16s}
button:hover{filter:brightness(1.07);transform:translateY(-1px)}
button.ghost{background:transparent;border:1px solid var(--line);
  color:var(--ink-soft);font-weight:400;font-size:14px;padding:10px 15px;
  margin-top:20px}
button.ghost:hover{background:var(--card);color:var(--accent-ink);filter:none;
  transform:none}
.row{display:flex;gap:10px;flex-wrap:wrap}
.row>*{flex:1 1 170px}
.err{color:#b5544a;font-size:13.5px;margin-top:12px}
.ok{color:var(--accent-ink);font-size:13.5px;margin-top:12px}
.hint{color:var(--ink-faint);font-size:12px;margin-top:5px;line-height:1.7}
.empty{color:var(--ink-soft);text-align:center;padding:48px 16px;line-height:2;
  font-size:15px}

.item{padding:12px 0;border-bottom:1px solid var(--line)}
.item:last-child{border-bottom:0}
.item a.title{color:var(--ink);text-decoration:none;font-size:15.5px;line-height:1.6}
.item a.title:hover{color:var(--accent-ink);text-decoration:underline;
  text-decoration-thickness:1px;text-underline-offset:3px}
.item .src{color:var(--ink-faint);font-size:12px;margin-top:2px}

.count-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(146px,1fr));
  gap:10px;margin-top:5px}
.count-card{padding:14px;border-radius:13px;background:var(--card);
  border:1px solid var(--line);box-shadow:var(--shadow);position:relative}
.count-card .n{font-size:28px;line-height:1.15;color:var(--accent-ink);
  font-weight:600}
.count-card .n small{font-size:13px;font-weight:400;margin-left:2px}
.count-card .t{font-size:13.5px;color:var(--ink);margin-top:4px}
.count-card .d{font-size:11.5px;color:var(--ink-faint);margin-top:2px}
.count-card.today{border-color:var(--accent)}
/* 删除按钮：两种卡片统一，别各写一套 */
.count-card form,.since-card form{position:absolute;top:3px;right:4px;margin:0}
.count-card form button,.since-card button.x{margin:0;padding:0 6px;
  min-height:28px;font-size:14px;line-height:1;background:transparent;
  border:1px solid transparent;color:var(--ink-faint);box-shadow:none}
.count-card form button:hover,.since-card button.x:hover{color:#b5544a;
  background:transparent;border-color:transparent;filter:none;
  transform:none;box-shadow:none}

.quote{padding:34px 24px;border-radius:16px;background:var(--sealed-bg);
  border:1px solid var(--line);box-shadow:var(--shadow);text-align:center;
  margin-bottom:16px}
.quote .body{font-size:21px;line-height:1.8;letter-spacing:.01em;margin:0 0 16px;
  text-wrap:balance;white-space:pre-line}
.quote .body.en{font-family:Georgia,"Times New Roman",serif;font-style:italic;
  font-size:20px;line-height:1.75}
.quote .author{color:var(--ink-soft);font-size:14px}
.quote .source{color:var(--ink-faint);font-size:12px;margin-top:4px}
.quote .lang-tag{display:inline-block;font-size:11px;letter-spacing:.08em;
  color:var(--ink-faint);border:1px solid var(--line);border-radius:99px;
  padding:1px 9px;margin-bottom:16px}

.sys-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));
  gap:10px;margin-top:8px}
.sys-cell{padding:13px;border-radius:12px;background:var(--card);
  border:1px solid var(--line)}
.sys-cell .k{font-size:11.5px;color:var(--ink-faint);letter-spacing:.04em}
.sys-cell .v{font-size:16.5px;color:var(--ink);margin-top:3px;font-weight:600;
  overflow-wrap:anywhere}
.sys-cell .v small{font-size:11.5px;font-weight:400;color:var(--ink-faint)}
.bar{height:5px;border-radius:99px;background:var(--line);margin-top:8px;
  overflow:hidden}
.bar i{display:block;height:100%;border-radius:99px;background:var(--accent)}

/* 主题选择：选中态由 :has() 决定，和 radio 的真实状态永远一致 */
.themes{display:grid;grid-template-columns:repeat(auto-fill,minmax(196px,1fr));
  gap:11px;margin-top:8px}
.theme-pick{position:relative;display:block;padding:14px;border-radius:13px;
  border:2px solid transparent;background:var(--card);cursor:pointer;
  outline:1px solid var(--line);outline-offset:-1px;
  transition:border-color .16s,transform .16s}
.theme-pick:hover{transform:translateY(-2px)}
.theme-pick input{position:absolute;opacity:0;pointer-events:none}
.theme-pick:has(input:checked){border-color:var(--accent);
  background:var(--card-hover)}
.theme-pick .sw{display:flex;gap:4px;margin-bottom:9px}
.theme-pick .sw i{width:20px;height:20px;border-radius:50%;display:block;
  border:1px solid rgba(0,0,0,.06)}
.theme-pick .nm{font-size:14px;font-weight:600}
.theme-pick .ds{font-size:11.5px;color:var(--ink-soft);margin-top:3px;
  line-height:1.6}

/* ---- 已经多久 ---- */
.since-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(238px,1fr));
  gap:11px;margin-top:5px}
.since-card{position:relative;padding:15px 17px;border-radius:13px;
  background:var(--card);border:1px solid var(--line);box-shadow:var(--shadow)}
.since-card .t{font-size:14px;color:var(--ink-soft);letter-spacing:.02em}
.since-card .big{font-size:23px;font-weight:600;color:var(--accent-ink);
  margin-top:5px;line-height:1.35;letter-spacing:.01em}
.since-card .d{font-size:11.5px;color:var(--ink-faint);margin-top:3px}
.since-card.small .big{font-size:19px}


/* ---- 热力图 ---- */
.heat{padding:16px 14px 12px;border-radius:14px;background:var(--card);
  border:1px solid var(--line);box-shadow:var(--shadow);margin:6px 0 18px}
.heat-head{display:flex;flex-wrap:wrap;gap:6px 16px;margin-bottom:12px}
.heat-stat{font-size:12.5px;color:var(--ink-soft);letter-spacing:.02em}
.heat-stat:first-child{color:var(--accent-ink);font-weight:600}
.heat-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;
  scrollbar-width:thin;padding-bottom:4px}
.heat-months{display:flex;gap:3px;margin-left:20px;min-width:max-content}
.heat-months span{width:11px;font-size:10px;color:var(--ink-faint);
  white-space:nowrap;overflow:visible;letter-spacing:0}
.heat-main{display:flex;gap:4px;align-items:flex-start}
.heat-weekdays{display:flex;flex-direction:column;gap:3px;width:16px;
  flex:0 0 16px;padding-top:1px}
.heat-weekdays span{height:11px;font-size:9.5px;color:var(--ink-faint);
  line-height:11px;text-align:right}
.heat-cols{display:flex;gap:3px;min-width:max-content}
.heat-col{display:flex;flex-direction:column;gap:3px}
.heat-cols i,.heat-cols a{width:11px;height:11px;border-radius:2.5px;
  display:block;background:var(--line);text-decoration:none}
.heat-cols a:hover{outline:1.5px solid var(--accent);outline-offset:1px}
.heat-cols .l1,.heat-legend .l1{background:color-mix(in srgb,var(--accent) 28%,var(--bg))}
.heat-cols .l2,.heat-legend .l2{background:color-mix(in srgb,var(--accent) 52%,var(--bg))}
.heat-cols .l3,.heat-legend .l3{background:color-mix(in srgb,var(--accent) 76%,var(--bg))}
.heat-cols .l4,.heat-legend .l4{background:var(--accent)}
.heat-cols .l0{background:var(--line)}
.heat-cols .future{background:transparent;border:1px solid var(--line);
  opacity:.35}
.heat-cols .today{outline:1.5px solid var(--accent-ink);outline-offset:1px}
.heat-legend{display:flex;align-items:center;gap:3px;margin-top:10px;
  font-size:10.5px;color:var(--ink-faint)}
.heat-legend i{width:10px;height:10px;border-radius:2.5px;display:block;
  background:var(--line)}
.heat-legend span{margin:0 4px}

/* ---- 单选一行（开机自启那种二选一） ---- */
.radio-row{display:flex;gap:9px;flex-wrap:wrap;align-items:center;
  margin-top:6px}
.radio-pick{display:inline-flex;align-items:center;gap:7px;margin:0;
  padding:10px 16px;border-radius:10px;border:2px solid var(--line);
  background:var(--card);cursor:pointer;font-size:14px;
  min-height:44px;transition:border-color .16s,background .16s}
.radio-pick input{width:auto;min-height:0;margin:0;accent-color:var(--accent)}
.radio-pick:has(input:checked){border-color:var(--accent);
  background:var(--card-hover);color:var(--accent-ink);font-weight:600}
.radio-row button{margin:0}

/* ---- 手记：一天多条 ---- */
.note-item{padding:12px 0;border-bottom:1px solid var(--line)}
.note-item:last-child{border-bottom:0}
.note-item .note-body{margin-top:4px;white-space:pre-wrap;
  overflow-wrap:anywhere;line-height:1.9}
.note-actions{display:flex;gap:10px;align-items:center;margin-top:7px}
.mini{font-size:12px;color:var(--ink-faint);text-decoration:none;
  background:none;border:0;padding:2px 4px;margin:0;min-height:0;
  cursor:pointer;font-family:inherit;box-shadow:none}
.mini:hover{color:var(--accent-ink);background:none;filter:none;
  transform:none;box-shadow:none}
.mini.danger:hover{color:#b5544a}
.date-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:8px}
.date-chip{font-size:12.5px;padding:6px 11px;border-radius:99px;
  border:1px solid var(--line);color:var(--ink-soft);text-decoration:none;
  background:var(--card);transition:border-color .16s,color .16s}
.date-chip:hover,.date-chip.on{border-color:var(--accent);
  color:var(--accent-ink)}
body.oil .date-chip{border-radius:2px;border-width:2px}
/* ---- 开关 ---- */
.switch{display:flex;align-items:center;gap:10px;margin:11px 0 0;
  font-size:14px;color:var(--ink);cursor:pointer;
  letter-spacing:.02em;min-height:32px}
.switch input{width:auto;min-height:0;margin:0;flex:0 0 auto;
  accent-color:var(--accent)}
.switch span{color:var(--ink)}

/* ---- 油画主题：硬色块、厚边框、位移阴影 ---- */
body.oil::before{background-image:
  linear-gradient(160deg,transparent 0 22%,var(--wash1) 22% 38%,transparent 38%),
  linear-gradient(20deg,transparent 0 55%,var(--wash2) 55% 72%,transparent 72%),
  linear-gradient(250deg,transparent 0 8%,var(--wash3) 8% 26%,transparent 26%),
  linear-gradient(340deg,transparent 0 78%,var(--wash4) 78% 92%,transparent 92%);
  opacity:.46}
body.oil .card,body.oil .sealed,body.oil .quote,body.oil .count-card,
body.oil .since-card,body.oil .sys-cell,body.oil .theme-pick,body.oil .heat{
  border-width:2px;border-radius:3px}
body.oil .card,body.oil .since-card,body.oil .count-card,body.oil .sys-cell,
body.oil .theme-pick,body.oil .heat,body.oil .sealed,body.oil .quote{
  box-shadow:5px 5px 0 rgba(35,32,27,0.20)}
body.oil a.card:hover{box-shadow:7px 7px 0 rgba(35,32,27,0.28);
  transform:translate(-1px,-1px)}
body.oil .dateline,body.oil .today{border-width:2px;border-radius:3px}
body.oil h1.brand{letter-spacing:.22em}
body.oil nav.main a{border-radius:2px}
body.oil button{border-radius:3px;border:2px solid var(--ink);
  box-shadow:3px 3px 0 rgba(35,32,27,0.26)}
body.oil button:hover{transform:translate(-1px,-1px);
  box-shadow:4px 4px 0 rgba(35,32,27,0.32)}
body.oil button.ghost{border-width:2px;box-shadow:2px 2px 0 rgba(35,32,27,0.14)}
body.oil input,body.oil textarea,body.oil select{border-width:2px;
  border-radius:3px;background:#fbf5e6}
body.oil .heat-cols i,body.oil .heat-cols a,body.oil .heat-legend i{
  border-radius:0}
body.oil .theme-pick{border-color:var(--ink)}
body.oil .theme-pick:has(input:checked){border-color:var(--accent);
  box-shadow:5px 5px 0 var(--accent)}
body.oil .bar{border-radius:0;border:1px solid var(--ink)}
body.oil .bar i{border-radius:0}
body.oil .quote .lang-tag,body.oil .tag{border-radius:0;border-width:2px}

/* ---- 日出主题：莫奈《印象·日出》那种冷灰雾港 + 一点橘 ---- */
body.sunrise::before{background-image:
  /* 那一轮橘红的太阳（放右上，避开正文卡片） */
  radial-gradient(circle 78px at 84% 15%,
    rgba(238,104,32,0.95) 0%, rgba(232,122,44,0.62) 44%, transparent 74%),
  /* 太阳外的暖光晕 */
  radial-gradient(circle 190px at 84% 15%,
    rgba(232,140,70,0.26) 0%, transparent 72%),
  /* 水面竖着的一道倒影 */
  linear-gradient(to bottom,
    rgba(232,110,40,0.30) 0%, rgba(232,110,40,0.14) 16%, transparent 38%),
  /* 雾一样的冷灰蓝，从左上压下来 */
  radial-gradient(ellipse 120% 75% at 12% 4%,
    rgba(108,132,152,0.58) 0%, transparent 68%),
  radial-gradient(ellipse 95% 62% at 92% 62%,
    rgba(86,116,120,0.42) 0%, transparent 66%),
  /* 下半部的水面，偏青灰 */
  linear-gradient(to top,
    rgba(78,104,116,0.42) 0%, rgba(130,152,158,0.28) 28%,
    rgba(178,192,196,0.12) 56%, transparent 80%)}
body.sunrise .card,body.sunrise .sealed,body.sunrise .quote,
body.sunrise .count-card,body.sunrise .since-card,body.sunrise .heat{
  border-color:rgba(92,110,124,0.30)}
body.sunrise .quote{background:
  linear-gradient(172deg,rgba(250,248,243,0.90),rgba(244,244,240,0.66))}
body.sunrise .dateline{background:rgba(250,249,244,0.82)}
body.sunrise .bar i{background:linear-gradient(
  to right,rgba(232,120,52,0.85),rgba(200,88,36,1))}
body.sunrise .count-card .n,body.sunrise .since-card .big{
  color:#b5511f}
/* ---- 背景轻微流动（可在设置里关掉） ---- */
@keyframes bgDrift {
  0%   {transform:scale(1) translate3d(0,0,0)}
  50%  {transform:scale(1.06) translate3d(-1.2%, -1%, 0)}
  100% {transform:scale(1) translate3d(0,0,0)}
}
body.bg-motion::before{animation:bgDrift 46s ease-in-out infinite;
  will-change:transform}
/* 系统要求减少动效时，无条件停掉 */
@media (prefers-reduced-motion:reduce){
  body.bg-motion::before{animation:none}
}
footer{margin-top:44px;color:var(--ink-faint);font-size:11.5px;text-align:center;
  letter-spacing:.12em}

@media (max-width:640px){
  .wrap{padding:18px 14px 52px}
  body{font-size:15.5px}
  h1.brand{font-size:17px}
  header{gap:6px;margin-bottom:16px}
  nav.main{width:100%;margin:0 -14px;padding:0 14px}
  article .letter{font-size:16.5px;line-height:2}
  .quote .body{font-size:18.5px}
  .quote .body.en{font-size:17.5px}
  .count-card .n{font-size:24px}
  .count-grid{grid-template-columns:repeat(auto-fill,minmax(132px,1fr))}
  .sys-grid{grid-template-columns:repeat(auto-fill,minmax(132px,1fr))}
}
"""


def font_key(font):
    return font if font in FONTS else DEFAULT_FONT


@functools.lru_cache(maxsize=16)
def css_for(theme_key, font="pixel"):
    theme = THEMES.get(theme_key) or THEMES[DEFAULT_THEME]
    face = FONTS.get(font_key(font))
    variables = "".join(f"--{k.replace('_', '-')}:{v};"
                        for k, v in theme["vars"].items())
    extra = face["extra"] or ""
    body_extra = f"body{{{extra}}}" if extra else ""
    return (":root{" + variables + f"--font:{face['stack']};}}\n"
            + BASE_CSS + body_extra)


def font_list():
    return [(k, f["name"], f["desc"]) for k, f in FONTS.items()]


def body_class(theme_key):
    """该主题给 <body> 加的类名（油画那套靠它切版式）。"""
    theme = THEMES.get(theme_key) or THEMES[DEFAULT_THEME]
    return theme.get("body_class", "")


def theme_list():
    return [(k, t["name"], t["desc"],
             [t["vars"][x] for x in ("bg", "wash1", "wash2", "accent")])
            for k, t in THEMES.items()]


if __name__ == "__main__":
    for key, name, desc, swatches in theme_list():
        print(f"{key:<12} {name:<12} {desc}")
    css = css_for("impression")
    print(f"\nCSS {len(css)} 字符，{len(css.encode())} 字节")
    # 自检：不该出现手机上会出事的写法
    problems = []
    if "background-attachment" in css:
        problems.append("background-attachment（iOS 渐变错位）")
    if "font-size:15px" in css.split("input,textarea,select")[-1][:400]:
        problems.append("输入框字号 <16px（iOS 自动放大）")
    print("移动端自检:", "通过" if not problems else "有问题 → " + "; ".join(problems))
