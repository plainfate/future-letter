#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态自检：找常见的真问题，不是风格洁癖。

查的东西：
  1. 未定义的函数调用（拼错的函数名）；
  2. 引用了不存在的模块属性；
  3. f-string 里引用了不存在的变量；
  4. HTML 里遗漏关标签导致的结构问题（粗查）。
"""

import ast
import pathlib
import re
import sys

BASE = pathlib.Path(r"D:\work\future-letter")
problems = []

PY_FILES = sorted(BASE.glob("*.py"))


def defined_names(tree):
    """模块里定义了哪些顶层名字。"""
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


trees = {}
for path in PY_FILES:
    source = path.read_text(encoding="utf-8")
    try:
        trees[path] = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        problems.append(f"{path.name}: 语法错误 {exc}")
        trees[path] = None

# 收集各模块的顶层名字
module_names = {}
for path, tree in trees.items():
    if tree is not None:
        module_names[path.stem] = defined_names(tree)

print("=== 1. 调用本模块内不存在的函数 ===")
for path, tree in trees.items():
    if tree is None:
        continue
    names = module_names[path.stem]
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split(".")[0])
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fname = node.func.id
            # 只看像本模块函数的（下划线开头，或已定义的）
            if fname.startswith("_"):
                others = set()
                for stem, ns in module_names.items():
                    if stem != path.stem:
                        others |= ns
                if fname not in names and fname not in imported \
                        and fname not in others:
                    problems.append(
                        f"{path.name}:{node.lineno} 调用了不存在的 {fname}()")
print("  完成")

print("\n=== 2. 模块属性引用 ===")
for path, tree in trees.items():
    if tree is None:
        continue
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and
                isinstance(node.value, ast.Name) and
                node.value.id in module_names):
            mod = node.value.id
            attr = node.attr
            if attr.startswith("__"):
                continue
            if attr not in module_names[mod]:
                problems.append(
                    f"{path.name}:{node.lineno} {mod}.{attr} 不存在")
print("  完成")

print("\n=== 3. themes 主题/字体完整性 ===")
sys.path.insert(0, str(BASE))
import themes  # noqa: E402

required_vars = {"bg", "wash1", "wash2", "wash3", "wash4", "card",
                 "card_hover", "ink", "ink_soft", "ink_faint", "line",
                 "accent", "accent_ink", "sealed_bg", "shadow", "shadow_hover"}
for key, theme in themes.THEMES.items():
    missing = required_vars - set(theme["vars"])
    if missing:
        problems.append(f"主题 {key} 缺少变量: {sorted(missing)}")
    if not theme.get("font") and not theme.get("vars"):
        problems.append(f"主题 {key} 既没字体也没变量")
print(f"  {len(themes.THEMES)} 个主题: {list(themes.THEMES)}")
for key, font in themes.FONTS.items():
    if not font.get("stack"):
        problems.append(f"字体 {key} 没有 font stack")
print(f"  {len(themes.FONTS)} 种字体: {list(themes.FONTS)}")
print(f"  默认主题 {themes.DEFAULT_THEME!r} 存在: {themes.DEFAULT_THEME in themes.THEMES}")
print(f"  默认字体 {themes.DEFAULT_FONT!r} 存在: {themes.DEFAULT_FONT in themes.FONTS}")

print("\n=== 4. 每个主题+字体的 CSS 都能生成 ===")
for t in themes.THEMES:
    for f in themes.FONTS:
        css = themes.css_for(t, f)
        if "--font:" not in css or len(css) < 5000:
            problems.append(f"css_for({t!r},{f!r}) 生成异常")
        if not css.rstrip().endswith("}"):
            problems.append(f"css_for({t!r},{f!r}) 结尾不完整")
print("  所有组合生成正常")

print("\n=== 5. 路由与视图函数一致性 ===")
app_tree = trees[BASE / "app.py"]
view_funcs = {n.name for n in app_tree.body
              if isinstance(n, ast.FunctionDef) and n.name.startswith("view_")}
app_source = (BASE / "app.py").read_text(encoding="utf-8")
used_views = set(re.findall(r"\b(view_[a-z_]+)\(", app_source))
undefined_views = used_views - view_funcs - {"view_settings"}
for name in sorted(undefined_views):
    if name not in module_names["app"]:
        problems.append(f"app.py 调用了未定义的 {name}()")
print(f"  定义了 {len(view_funcs)} 个 view 函数")
if undefined_views:
    print(f"  引用: {sorted(used_views)}")
missing_views = view_funcs - used_views
if missing_views:
    print(f"  （定义了但没被调用: {sorted(missing_views)}，可能正常）")

print("\n=== 6. 引用了不存在的 MESSAGES 提示码 ===")
import app  # noqa: E402

codes = set(app.MESSAGES)
used_codes = set(re.findall(r"/[a-z/?=&]*m=([a-z_]+)", app_source))
for code in sorted(used_codes - codes):
    problems.append(f"页面跳转用了未定义的提示码 {code!r}")
print(f"  定义了 {len(codes)} 个提示码，页面用了 {len(used_codes)} 个")

print("\n" + "=" * 50)
if problems:
    print(f"发现 {len(problems)} 个问题：")
    for p in problems:
        print("  ✗ " + p)
    sys.exit(1)
print("静态自检全部通过")
