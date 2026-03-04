#!/usr/bin/env python3
import argparse
import os
import sys
import time
import requests

CF_API = "https://api.cloudflare.com/client/v4"


def cf_request(token: str, method: str, url: str, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    r = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    return r


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--zone-id", required=True)
    p.add_argument("--token", required=False, default=os.getenv("CLOUDFLARE_TOKEN", ""))
    p.add_argument("--name", required=True, help="FQDN, e.g. admin.fscitech.net")
    p.add_argument("--target", required=True, help="CNAME target, e.g. futuretechquant.github.io")
    p.add_argument("--proxied", choices=["true", "false"], default="false")
    args = p.parse_args()

    if not args.token:
        print("ERROR: missing Cloudflare token", file=sys.stderr)
        return 2

    proxied = (args.proxied == "true")

    # Find existing record
    list_url = f"{CF_API}/zones/{args.zone_id}/dns_records"
    r = cf_request(args.token, "GET", list_url, params={"type": "CNAME", "name": args.name})
    if r.status_code != 200:
        print("ERROR: list dns_records failed:", r.status_code, r.text, file=sys.stderr)
        return 1
    data = r.json()
    if not data.get("success"):
        print("ERROR: list dns_records not success:", r.text, file=sys.stderr)
        return 1

    rec_id = ""
    results = data.get("result") or []
    if results:
        rec_id = results[0].get("id", "")

    payload = {
        "type": "CNAME",
        "name": args.name,
        "content": args.target,
        "ttl": 1,          # auto
        "proxied": proxied
    }

    if rec_id:
        url = f"{CF_API}/zones/{args.zone_id}/dns_records/{rec_id}"
        r2 = cf_request(args.token, "PUT", url, json=payload)
        if r2.status_code != 200:
            print("ERROR: update dns_record failed:", r2.status_code, r2.text, file=sys.stderr)
            return 1
        j = r2.json()
        if not j.get("success"):
            print("ERROR: update dns_record not success:", r2.text, file=sys.stderr)
            return 1
        print(f"OK: updated CNAME {args.name} -> {args.target} proxied={proxied}")
        return 0

    url = f"{CF_API}/zones/{args.zone_id}/dns_records"
    r3 = cf_request(args.token, "POST", url, json=payload)
    if r3.status_code not in (200, 201):
        print("ERROR: create dns_record failed:", r3.status_code, r3.text, file=sys.stderr)
        return 1
    j = r3.json()
    if not j.get("success"):
        print("ERROR: create dns_record not success:", r3.text, file=sys.stderr)
        return 1

    print(f"OK: created CNAME {args.name} -> {args.target} proxied={proxied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
