#!/usr/bin/env python3
"""
将 HBuilderX uni-app Vue3 项目转换为 CLI (Vite) 项目。
在项目根目录执行，幂等，可安全重复运行。
"""
import os, json, shutil, re

ROOT_KEEP = {
    "vite.config.ts", "vite.config.js",
    "tsconfig.json", "tsconfig.node.json",
    "package.json", "package-lock.json",
    "pnpm-lock.yaml", "yarn.lock",
    ".npmrc", ".nvmrc", ".node-version",
    "index.html",
    ".git", ".gitignore", ".gitattributes",
    ".github", ".gitee",
    "node_modules", "dist", "unpackage",
    ".env", ".env.local", ".env.development", ".env.production",
    "README.md", "LICENSE",
}

CLI_SCRIPTS = {
    "dev:h5":          "uni",
    "build:h5":        "uni build",
    "dev:mp-weixin":   "uni -p mp-weixin",
    "build:mp-weixin": "uni build -p mp-weixin",
    "dev:app":         "uni -p app",
    "build:app":       "uni build -p app",
    "build:app-plus":  "uni build -p app-plus",
}

CLI_EXTRA_DEPS = {
    "@dcloudio/uni-app": "*",
}

CLI_EXTRA_DEV_DEPS = {
    "@dcloudio/vite-plugin-uni": "*",
    "@dcloudio/uni-h5":          "*",
    "@dcloudio/uni-mp-weixin":   "*",
    "@dcloudio/uni-app-plus":    "*",
    "@dcloudio/types":           "*",
    "vite":                      "^5.2.8",
    "typescript":                "^5.2.0",
    "vue":                       "^3.4.0",
    "sass":                      "^1.77.0",
}

# 仅在原项目无 vite.config 时使用此模板
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
    for item in sorted(os.listdir(".")):
        if item in ROOT_KEEP or item == "src":
            continue
        if item.startswith("."):
            continue
        dest = os.path.join("src", item)
        if os.path.exists(dest):
            print(f"  [skip]  {item}（src/ 中已存在）")
            continue
        shutil.move(item, dest)
        print(f"  [moved] {item} → src/{item}")


def fix_index_html():
    if not os.path.exists("index.html"):
        print("  [skip]  index.html 不存在")
        return
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    new_content = content
    for entry in ("main.ts", "main.js"):
        new_content = new_content.replace(f'"/{entry}"',  f'"/src/{entry}"')
        new_content = new_content.replace(f"'/{entry}'",  f"'/src/{entry}'")
        new_content = new_content.replace(f'"./{entry}"', f'"./src/{entry}"')
        new_content = new_content.replace(f"'./{entry}'", f"'./src/{entry}'")
    if new_content != content:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("  [fixed] index.html 入口路径已修正为 src/")
    else:
        print("  [skip]  index.html 路径无需修正")


def create_vite_config():
    """
    优先保留原始 vite.config.js（含 ROUTES_MAP define、loadEnv 等），
    将所有相对路径引用由根目录修正为 src/（含自定义插件 import）。
    若无原始配置则创建标准模板。
    """
    patched = False
    for cfg in ("vite.config.js", "vite.config.ts"):
        if not os.path.exists(cfg):
            continue
        with open(cfg, "r", encoding="utf-8") as f:
            content = f.read()
        new_content = content

        # ── 固定字段路径修正 ──────────────────────────────────────────
        new_content = new_content.replace("inputDir: '.'",  "inputDir: 'src'")
        new_content = new_content.replace('inputDir: "."',  'inputDir: "src"')
        new_content = new_content.replace("'./pages.json'",    "'./src/pages.json'")
        new_content = new_content.replace('"./pages.json"',    '"./src/pages.json"')
        new_content = new_content.replace("'./manifest.json'", "'./src/manifest.json'")
        new_content = new_content.replace('"./manifest.json"', '"./src/manifest.json"')

        # ── 通用相对路径修正（import/require 指向已迁移至 src/ 的文件）──
        # 匹配：from './foo'  |  from "./foo"
        #       require('./foo')  |  require("./foo")
        # 跳过：已经是 ./src/  |  npm 包（无 ./ 前缀）
        new_content = re.sub(
            r"""((?:from\s+|require\s*\(\s*)['"])\./((?!src/)(?!node_modules/))""",
            r"\1./src/",
            new_content,
        )

        with open(cfg, "w", encoding="utf-8") as f:
            f.write(new_content)
        if new_content != content:
            print(f"  [patched] {cfg}（路径已修正为 src/）")
        else:
            print(f"  [kept]    {cfg}（无需修改）")
        patched = True
        break

    if not patched:
        with open("vite.config.ts", "w", encoding="utf-8") as f:
            f.write(VITE_CONFIG)
        print("  [created] vite.config.ts（标准模板）")


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

    existing_scripts = pkg.get("scripts", {})
    for k, v in CLI_SCRIPTS.items():
        existing_scripts.setdefault(k, v)
    pkg["scripts"] = existing_scripts

    deps     = pkg.setdefault("dependencies", {})
    dev_deps = pkg.setdefault("devDependencies", {})

    for k, v in CLI_EXTRA_DEPS.items():
        deps.setdefault(k, v)
    for k, v in CLI_EXTRA_DEV_DEPS.items():
        dev_deps.setdefault(k, v)

    print("  [deps]    ", list(deps.keys()))
    print("  [devDeps] ", list(dev_deps.keys()))

    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(pkg, f, ensure_ascii=False, indent=2)
    print("  [updated] package.json")

    src_pkg_path = os.path.join("src", "package.json")
    if os.path.exists("src"):
        shutil.copy2(pkg_path, src_pkg_path)
        print("  [copied]  package.json → src/package.json（供源码内部引用）")


def verify_src_manifest():
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
    fix_index_html()
    create_vite_config()   # 保留原始配置，只修正路径
    create_npmrc()
    update_package_json()
    verify_src_manifest()
    print("✅ 转换完成！源码已迁移至 src/")


if __name__ == "__main__":
    main()
