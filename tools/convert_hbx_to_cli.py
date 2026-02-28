#!/usr/bin/env python3
"""
将 HBuilderX uni-app Vue3 项目转换为 CLI (Vite) 项目。
在项目根目录执行，幂等，可安全重复运行。
"""
import os, json, shutil

SRC_ITEMS = [
    "pages", "components", "static", "store", "stores",
    "utils", "api", "hooks", "types", "assets", "locale",
    "uni_modules", "hybrid",
    "App.vue", "main.js", "main.ts",
    "pages.json", "manifest.json",
    "uni.scss", "uni.css",
    "index.html",
]

CLI_SCRIPTS = {
    "dev:h5":          "uni",
    "build:h5":        "uni build",
    "dev:mp-weixin":   "uni -p mp-weixin",
    "build:mp-weixin": "uni build -p mp-weixin",
    "dev:app":         "uni -p app",
    "build:app":       "uni build -p app",
    "build:app-plus":  "uni build -p app-plus",
}

CLI_DEPS = {
    "@dcloudio/uni-app": "*",
}

CLI_DEV_DEPS = {
    "@dcloudio/vite-plugin-uni": "*",
    "@dcloudio/uni-h5":          "*",
    "@dcloudio/uni-mp-weixin":   "*",
    "@dcloudio/uni-app-plus":    "*",
    "@dcloudio/types":           "*",
    "vite":                      "^5.2.8",
    "typescript":                "^5.2.0",
    "vue":                       "^3.4.0",   # CLI 项目必须显式声明，HBuilderX 由 IDE 内置
}

VITE_CONFIG = """\
import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
})
"""

NPMRC = """\
strict-peer-dependencies=false
shamefully-hoist=true
"""


def is_cli_project() -> bool:
    """
    必须同时满足：
    1. 有 vite config（vite.config.ts 或 .js）
    2. src/ 下已有 manifest.json 或 pages.json
    防止"原项目带 vite.config.js 但文件仍在根目录"时误判跳过迁移。
    """
    has_vite = (
        os.path.exists("vite.config.ts")
        or os.path.exists("vite.config.js")
    )
    has_src = (
        os.path.exists("src/manifest.json")
        or os.path.exists("src/pages.json")
    )
    return has_vite and has_src


def move_to_src():
    os.makedirs("src", exist_ok=True)
    for item in SRC_ITEMS:
        if not os.path.exists(item):
            continue
        dest = os.path.join("src", item)
        if os.path.exists(dest):
            print(f"  [skip]  {item}（src/ 中已存在）")
            continue
        shutil.move(item, dest)
        print(f"  [moved] {item} → src/{item}")


def create_vite_config():
    # 强制删除旧的 vite.config.js/.ts
    # 原始项目的 vite.config.js 可能指向根目录，与迁移后的 src/ 结构不符
    for old_cfg in ("vite.config.js", "vite.config.ts"):
        if os.path.exists(old_cfg):
            os.remove(old_cfg)
            print(f"  [removed] {old_cfg}（替换为标准 CLI 配置）")
    with open("vite.config.ts", "w", encoding="utf-8") as f:
        f.write(VITE_CONFIG)
    print("  [created] vite.config.ts")


def create_npmrc():
    if not os.path.exists(".npmrc"):
        with open(".npmrc", "w", encoding="utf-8") as f:
            f.write(NPMRC)
        print("  [created] .npmrc")


def update_package_json():
    pkg_path = "package.json"
    if os.path.exists(pkg_path):
        with open(pkg_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
    else:
        pkg = {"name": "future-mall-uniapp", "version": "1.0.0", "private": True}

    existing = pkg.get("scripts", {})
    for k, v in CLI_SCRIPTS.items():
        existing.setdefault(k, v)
    pkg["scripts"] = existing

    pkg.setdefault("dependencies", {}).update(CLI_DEPS)
    pkg.setdefault("devDependencies", {}).update(CLI_DEV_DEPS)

    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(pkg, f, ensure_ascii=False, indent=2)
    print("  [updated] package.json")


def verify_src_manifest():
    """转换完成后校验 src/manifest.json 必须存在，否则终止。"""
    if not os.path.exists("src/manifest.json"):
        raise FileNotFoundError(
            "❌ 转换后 src/manifest.json 仍不存在！"
            "请检查源项目中是否包含 manifest.json。"
        )
    print("  [verified] src/manifest.json ✅")


def main():
    if is_cli_project():
        print("✅ 已是 CLI 项目，跳过文件迁移，仅补充 scripts/依赖...")
        update_package_json()
        create_npmrc()
        verify_src_manifest()
        return

    print("🔄 开始 HBuilderX → CLI 项目转换...")
    move_to_src()
    create_vite_config()   # 强制覆盖，确保 inputDir 默认指向 src/
    create_npmrc()
    update_package_json()
    verify_src_manifest()
    print("✅ 转换完成！源码已迁移至 src/")


if __name__ == "__main__":
    main()
