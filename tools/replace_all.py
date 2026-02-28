#!/usr/bin/env python3
"""
Replace brand names and API URLs in all text files under current directory.
"""
import os
import re

# 替换规则（顺序很重要：长词/大小写精确匹配优先）
REPLACEMENTS = [
    # ✅ URL 替换必须放最前面（精确匹配，避免被后面的通用规则破坏）
    ("http://api-dashboard.yudao.iocoder.cn",  "https://shanxigaokaozixun.com"),
    ("http://mall.yudao.iocoder.cn",           "https://shanxigaokaozixun.com"),
    ("http://localhost:48080",           "https://shanxigaokaozixun.com"),
    ("http://127.0.0.1:3000",           "http://114.55.24.12:3000"),
    # 品牌名替换（大写/长词优先）
    ("RuoYi",  "Future"),
    ("Ruoyi",  "Future"),
    ("ruoyi",  "future"),
    ("Yudao",  "Future"),
    ("yudao",  "future"),
]

# 需要跳过的二进制/不可处理文件后缀
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz",
    ".jar", ".class",
    ".lock",          # package-lock.json / yarn.lock 可视需求决定是否跳过
}

# 需要跳过的目录
SKIP_DIRS = {"node_modules", ".git", "dist", ".cache"}


def process_file(path: str) -> None:
    ext = os.path.splitext(path)[1].lower()
    if ext in SKIP_EXTENSIONS:
        return
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError):
        return  # 跳过二进制或无权限文件

    new_content = content
    for old, new in REPLACEMENTS:
        new_content = new_content.replace(old, new)

    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  [replaced] {path}")


def main():
    root = os.getcwd()
    for dirpath, dirnames, filenames in os.walk(root):
        # 原地修改 dirnames 以跳过指定目录
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            process_file(os.path.join(dirpath, filename))


if __name__ == "__main__":
    main()
