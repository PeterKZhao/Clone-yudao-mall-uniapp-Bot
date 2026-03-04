#!/usr/bin/env python3
import argparse
import os
import sys
import time
import requests


def gh(method, url, token, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.update({
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    return requests.request(method, url, headers=headers, timeout=30, **kwargs)


def enable_pages(org, repo, token, branch):
    base = f"https://api.github.com/repos/{org}/{repo}/pages"
    payload = {"build_type": "workflow", "source": {"branch": branch, "path": "/"}}

    # Create (ignore if exists)
    r1 = gh("POST", base, token, json=payload)
    if r1.status_code not in (201, 409, 422):
        # 422 有时表示“已存在/参数冲突”，不必硬失败，继续 PUT 修正
        print("WARN: POST /pages:", r1.status_code, r1.text)

    # Force update
    r2 = gh("PUT", base, token, json=payload)
    if r2.status_code not in (200, 204):
        raise RuntimeError(f"PUT /pages failed: {r2.status_code} {r2.text}")


def set_cname(org, repo, token, branch, cname):
    base = f"https://api.github.com/repos/{org}/{repo}/pages"
    payload = {"cname": cname, "build_type": "workflow", "source": {"branch": branch, "path": "/"}}

    # GitHub 有时会在证书未就绪阶段返回 404 + “The certificate does not exist yet”
    for i in range(1, 31):
        r = gh("PUT", base, token, json=payload)
        if r.status_code in (200, 204):
            return
        if r.status_code == 404 and "certificate does not exist yet" in r.text.lower():
            time.sleep(20)
            continue
        raise RuntimeError(f"Set cname failed: {r.status_code} {r.text}")
    print("WARN: set cname timeout; rerun workflow later")


def wait_cert(org, repo, token, timeout_sec=15 * 60):
    base = f"https://api.github.com/repos/{org}/{repo}/pages"
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        r = gh("GET", base, token)
        if r.status_code == 200:
            j = r.json()
            cert = j.get("https_certificate")
            if cert is not None:
                return True
        time.sleep(10)
    return False


def enforce_https(org, repo, token, branch, cname):
    base = f"https://api.github.com/repos/{org}/{repo}/pages"
    payload = {
        "cname": cname,
        "https_enforced": True,
        "build_type": "workflow",
        "source": {"branch": branch, "path": "/"},
    }

    for i in range(1, 31):  # 最多等 10 分钟（30 * 20s）
        r = gh("PUT", base, token, json=payload)
        if r.status_code in (200, 204):
            return

        msg = (r.text or "").lower()
        cert_not_ready = (
            r.status_code == 404 and (
                "certificate does not exist yet" in msg or
                "certificate has not finished being issued" in msg
            )
        )
        if cert_not_ready:
            print(f"WARN: certificate not ready yet ({i}/30), sleep 20s...")
            time.sleep(20)
            continue

        raise RuntimeError(f"enforce_https failed: {r.status_code} {r.text}")

    print("WARN: cert still not ready; rerun workflow later to enforce https")
    return

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--org", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--token", default=os.getenv("APP_TOKEN", ""))
    p.add_argument("--cname", default="")
    p.add_argument("--enforce-https", choices=["true", "false"], default="true")
    args = p.parse_args()

    if not args.token:
        print("ERROR: missing APP_TOKEN", file=sys.stderr)
        return 2

    enable_pages(args.org, args.repo, args.token, args.branch)

    if not args.cname:
        print("No cname, done.")
        return 0

    set_cname(args.org, args.repo, args.token, args.branch, args.cname)

    if args.enforce_https != "true":
        print("enforce_https=false, done.")
        return 0

    if not wait_cert(args.org, args.repo, args.token, timeout_sec=20 * 60):
        print("WARN: cert not ready in time; rerun later to enforce https")
        return 0

    enforce_https(args.org, args.repo, args.token, args.branch, args.cname)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
