#!/usr/bin/env python3
"""
Replace brand names and API URLs in all text files under current directory.
Tuned for yudao-mall-uniapp migration.
"""
import os

# 替换规则（顺序很重要：长词 / 精确 URL 优先，防止被后续规则破坏）
REPLACEMENTS = [
    # ── API 地址替换 ─────────────────────────────────────────────────────────
    # mall 项目默认后端地址
    ("http://api-dashboard.yudao.iocoder.cn",   "https://shanxigaokaozixun.com"),
    ("http://mall.yudao.iocoder.cn",            "https://shanxigaokaozixun.com"),
    ("http://localhost:48080",                  "https://shanxigaokaozixun.com"),
    ("http://127.0.0.1:48080",                  "https://shanxigaokaozixun.com"),
    ("http://127.0.0.1:3000",                   "http://114.55.24.12:3000"),
    # uniapp 默认请求前缀（manifest.json / request.js 中可能出现）
    ("https://api.iocoder.cn",                  "https://shanxigaokaozixun.com"),

    # ── 品牌名替换（长词 / 大写优先）────────────────────────────────────────
    ("芋道商城",   "Future 商城"),
    ("芋道源码",   "Future"),
    ("芋道",       "Future"),
    ("RuoYi",      "Future"),
    ("Ruoyi",      "Future"),
    ("ruoyi",      "future"),
    ("Yudao",      "Future"),
    ("yudao",      "future"),
    # 小程序 AppID 占位（manifest.json 中按需替换）
    # ("wxXXXXXXXXXXXXXXXX",  "wx你的真实AppID"),
]

# 跳过的二进制 / 锁文件后缀
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".rar",
    ".jar", ".class",
    ".mp3", ".mp4", ".wav",
    ".lock",
}

# 跳过的目录
SKIP_DIRS = {"node_modules", ".git", "dist", ".cache", "unpackage"}


def process_file(path: str) -> None:
    ext = os.path.splitext(path)[1].lower()
    if ext in SKIP_EXTENSIONS:
        return
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError):
        return

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
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            process_file(os.path.join(dirpath, filename))


if __name__ == "__main__":
    main()
