#!/usr/bin/env python3
"""
Dashboard Mirror
Builds a local report that approximates what you'd see in the dashboard by combining:
1) Public page snapshot (title, headings, links, visible text excerpt)
2) Coordinator health API data
3) Authenticated Bankr agent status (if BANKR_API_KEY is available)

Usage:
  python dashboard_mirror.py
  python dashboard_mirror.py --url "https://www.litcoiin.xyz/dashboard?tab=agents"
  python dashboard_mirror.py --out-dir reports --text-limit 3000
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

import requests

DEFAULT_DASHBOARD_URL = "https://www.litcoiin.xyz/dashboard?tab=agents"
DEFAULT_HEALTH_URL = "https://api.litcoiin.xyz/v1/health"
BANKR_ME_URL = "https://api.bankr.bot/agent/me"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_request(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> dict[str, Any]:
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        content_type = response.headers.get("content-type", "")
        body = response.text
        parsed_json = None
        if "application/json" in content_type.lower():
            try:
                parsed_json = response.json()
            except Exception:
                parsed_json = None
        return {
            "ok": True,
            "status_code": response.status_code,
            "url": response.url,
            "content_type": content_type,
            "headers": {
                "server": response.headers.get("server", ""),
                "cache_control": response.headers.get("cache-control", ""),
            },
            "text": body,
            "json": parsed_json,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "status_code": None,
            "url": url,
            "content_type": None,
            "headers": {},
            "text": "",
            "json": None,
        }


def parse_html_snapshot(html: str, text_limit: int = 2500, link_limit: int = 40) -> dict[str, Any]:
    # Remove script/style blocks so visible text is cleaner.
    clean = re.sub(r"<script[\\s\\S]*?</script>", " ", html, flags=re.IGNORECASE)
    clean = re.sub(r"<style[\\s\\S]*?</style>", " ", clean, flags=re.IGNORECASE)

    title_match = re.search(r"<title[^>]*>([\\s\\S]*?)</title>", clean, flags=re.IGNORECASE)
    title = unescape(title_match.group(1).strip()) if title_match else ""

    heading_matches = re.findall(
        r"<(h1|h2|h3)[^>]*>([\\s\\S]*?)</\\1>", clean, flags=re.IGNORECASE
    )
    headings: list[str] = []
    for _, raw in heading_matches:
        text = re.sub(r"<[^>]+>", " ", raw)
        text = re.sub(r"\\s+", " ", unescape(text)).strip()
        if text and text not in headings:
            headings.append(text)

    link_matches = re.findall(r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>([\\s\\S]*?)</a>", clean, flags=re.IGNORECASE)
    links: list[dict[str, str]] = []
    for href, label_raw in link_matches:
        label = re.sub(r"<[^>]+>", " ", label_raw)
        label = re.sub(r"\\s+", " ", unescape(label)).strip()
        if not href:
            continue
        links.append({"href": href, "label": label})
        if len(links) >= link_limit:
            break

    visible_text = re.sub(r"<[^>]+>", " ", clean)
    visible_text = re.sub(r"\\s+", " ", unescape(visible_text)).strip()

    return {
        "title": title,
        "headings": headings[:30],
        "links": links,
        "visible_text_excerpt": visible_text[:text_limit],
    }


def get_bankr_status(api_key: str | None) -> dict[str, Any]:
    if not api_key:
        return {
            "available": False,
            "reason": "BANKR_API_KEY not set",
            "auth_ok": False,
        }

    masked = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "[masked]"

    # Try X-API-Key first; fallback to Bearer if needed.
    headers_x = {"X-API-Key": api_key, "Content-Type": "application/json"}
    first = safe_request(BANKR_ME_URL, headers=headers_x)

    if first.get("status_code") == 200:
        return {
            "available": True,
            "auth_ok": True,
            "method": "X-API-Key",
            "key_mask": masked,
            "status_code": 200,
            "data": first.get("json") or {},
        }

    headers_bearer = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    second = safe_request(BANKR_ME_URL, headers=headers_bearer)

    return {
        "available": True,
        "auth_ok": second.get("status_code") == 200,
        "method": "Bearer",
        "key_mask": masked,
        "status_code": second.get("status_code"),
        "error": (second.get("json") or {}).get("message") if second.get("json") else second.get("error"),
        "data": second.get("json") or {},
    }


def build_markdown(report: dict[str, Any]) -> str:
    dashboard = report.get("dashboard", {})
    page = dashboard.get("page", {})
    snap = dashboard.get("snapshot", {})
    health = report.get("coordinator_health", {})
    bankr = report.get("bankr", {})

    lines: list[str] = []
    lines.append("# Dashboard Mirror Report")
    lines.append("")
    lines.append(f"- Generated: {report.get('generated_at_utc', '')}")
    lines.append(f"- Dashboard URL: {dashboard.get('url', '')}")
    lines.append(f"- Dashboard HTTP: {page.get('status_code', 'n/a')}")
    lines.append(f"- Coordinator Health HTTP: {health.get('status_code', 'n/a')}")
    lines.append(f"- Bankr Auth: {'OK' if bankr.get('auth_ok') else 'FAILED'}")
    lines.append("")

    lines.append("## Dashboard Snapshot")
    lines.append(f"- Title: {snap.get('title', '')}")
    if not snap.get("headings") and not snap.get("links"):
        lines.append("- Note: this page appears JS-rendered, so server HTML contains minimal visible data.")
    headings = snap.get("headings", [])
    if headings:
        lines.append("- Headings:")
        for h in headings[:12]:
            lines.append(f"  - {h}")
    links = snap.get("links", [])
    if links:
        lines.append("- Sample links:")
        for link in links[:12]:
            label = link.get("label") or "(no label)"
            href = link.get("href") or ""
            lines.append(f"  - {label}: {href}")

    excerpt = snap.get("visible_text_excerpt", "")
    if excerpt:
        lines.append("")
        lines.append("## Visible Text Excerpt")
        lines.append("")
        lines.append(excerpt)

    if health.get("json"):
        j = health["json"]
        lines.append("")
        lines.append("## Coordinator Health")
        lines.append(f"- Status: {j.get('status', 'n/a')}")
        lines.append(f"- Chain: {j.get('chain', 'n/a')}")
        lines.append(f"- Epoch: {j.get('epoch', 'n/a')}")
        lines.append(f"- Build: {j.get('build', 'n/a')}")
        lines.append(f"- Active Tasks: {((j.get('research') or {}).get('activeTasks', 'n/a'))}")
        lines.append(f"- Total Miners: {((j.get('claims') or {}).get('totalMiners', 'n/a'))}")

    if bankr.get("available"):
        lines.append("")
        lines.append("## Bankr Agent Status")
        lines.append(f"- Auth OK: {bankr.get('auth_ok')}")
        lines.append(f"- Method: {bankr.get('method', 'n/a')}")
        lines.append(f"- Key: {bankr.get('key_mask', '[masked]')}")
        lines.append(f"- HTTP: {bankr.get('status_code', 'n/a')}")

        data = bankr.get("data") or {}
        if data:
            wallet = data.get("wallet")
            if not wallet:
                wallets = data.get("wallets") or []
                if isinstance(wallets, list) and wallets:
                    evm_wallet = next((w.get("address") for w in wallets if isinstance(w, dict) and w.get("chain") == "evm"), None)
                    wallet = evm_wallet or (wallets[0].get("address") if isinstance(wallets[0], dict) else None)
            lines.append(f"- Wallet: {wallet or 'n/a'}")
            lines.append(f"- Total Earned: {data.get('totalEarnedFormatted', data.get('totalEarned', 'n/a'))}")
            lines.append(f"- Claimable: {data.get('claimableFormatted', data.get('claimable', 'n/a'))}")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Mirror LITCOIN dashboard + status into local reports")
    parser.add_argument("--url", default=DEFAULT_DASHBOARD_URL, help="Dashboard URL to mirror")
    parser.add_argument("--health-url", default=DEFAULT_HEALTH_URL, help="Coordinator health API URL")
    parser.add_argument("--out-dir", default="reports", help="Output directory")
    parser.add_argument("--text-limit", type=int, default=2500, help="Visible text excerpt length")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    ua = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    }

    page = safe_request(args.url, headers=ua)
    snapshot = parse_html_snapshot(page.get("text", ""), text_limit=args.text_limit)

    health = safe_request(args.health_url, headers=ua)

    bankr_key = os.getenv("BANKR_API_KEY") or os.getenv("BANKR_KEY")
    bankr = get_bankr_status(bankr_key)

    report = {
        "generated_at_utc": now_utc(),
        "dashboard": {
            "url": args.url,
            "page": {
                "status_code": page.get("status_code"),
                "content_type": page.get("content_type"),
                "ok": page.get("ok"),
                "error": page.get("error"),
            },
            "snapshot": snapshot,
        },
        "coordinator_health": {
            "status_code": health.get("status_code"),
            "content_type": health.get("content_type"),
            "ok": health.get("ok"),
            "error": health.get("error"),
            "json": health.get("json"),
        },
        "bankr": bankr,
        "operational": bool(bankr.get("auth_ok")),
    }

    json_path = out_dir / f"dashboard_mirror_{stamp}.json"
    md_path = out_dir / f"dashboard_mirror_{stamp}.md"

    html_path = out_dir / f"dashboard_mirror_{stamp}.html"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_markdown(report))

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page.get("text", ""))

    print(f"Report JSON: {json_path}")
    print(f"Report MD:   {md_path}")
    print(f"Page HTML:   {html_path}")
    print(f"Operational: {report['operational']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
