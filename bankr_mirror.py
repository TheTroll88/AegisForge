#!/usr/bin/env python3
"""
Bankr Mirror
Collects what we can from Bankr and local miner state into one report.

Data sources:
1) Bankr agent API via BANKR_API_KEY (api.bankr.bot/agent/me)
2) Optional LLM gateway probe via BANKR_LLM_KEY on /llm/usage
3) Optional authenticated web snapshots of Bankr tabs via BANKR_SESSION_COOKIE
4) Local miner status via litcoin SDK status()

Usage:
  python bankr_mirror.py
  python bankr_mirror.py --out-dir reports --text-limit 3000

Environment variables:
  BANKR_API_KEY         Agent API key (bk_...) for /agent/me
  BANKR_LLM_KEY         LLM gateway key (if different from BANKR_API_KEY)
  BANKR_SESSION_COOKIE  Browser session cookie string for bankr.bot
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

BANKR_AGENT_ME_URL = "https://api.bankr.bot/agent/me"
BANKR_LLM_USAGE_URL = "https://api.bankr.bot/llm/usage"
BANKR_BROWSER_API_ENDPOINTS = [
    ("user", "https://api.bankr.bot/user"),
    ("activity", "https://api.bankr.bot/user/activity"),
    ("assets", "https://api.bankr.bot/user/assets"),
    ("widgets", "https://api.bankr.bot/user/widgets"),
    ("doppler_v4", "https://api.bankr.bot/user/doppler/v4"),
    ("automation_agent_command", "https://api.bankr.bot/user/automation?skip=0&types=agent_command"),
    (
        "automation_orders",
        "https://api.bankr.bot/user/automation?skip=0&types=order&subTypes=stop-sell%2Cstop-buy%2Climit-sell%2Climit-buy%2Cdca%2Ctwap",
    ),
    ("security_module", "https://api.bankr.bot/bankr-security-module/data"),
    ("user_sol", "https://api.bankr.bot/user/sol"),
    ("llm_usage_30d", "https://api.bankr.bot/llm/usage?days=30"),
    ("public_llm_rankings_30d", "https://api.bankr.bot/public/llm/rankings?days=30"),
    ("public_llm_models_health", "https://api.bankr.bot/public/llm/models/health"),
]
BANKR_WEB_TABS = [
    "https://bankr.bot/llm",
    "https://bankr.bot/api",
    "https://bankr.bot/agent",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_privy_token_expiry(cookie_string: str | None) -> dict[str, Any]:
    """Extract expiry info from the privy-token JWT in a cookie string."""
    if not cookie_string:
        return {"found": False}
    match = re.search(r"privy-token=([^;]+)", cookie_string)
    if not match:
        return {"found": False}
    parts = match.group(1).split(".")
    if len(parts) < 2:
        return {"found": False, "error": "malformed JWT"}
    try:
        payload_b64 = parts[1]
        pad = 4 - len(payload_b64) % 4
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * pad))
        exp = payload.get("exp", 0)
        now = time.time()
        seconds_left = exp - now
        return {
            "found": True,
            "expires_utc": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat(),
            "seconds_remaining": int(seconds_left),
            "minutes_remaining": round(seconds_left / 60, 1),
            "expired": seconds_left < 0,
            "session_id": payload.get("sid", ""),
        }
    except Exception as exc:
        return {"found": True, "error": str(exc)}


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
            "ok": response.ok,
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


def build_browser_headers(url: str, session_cookie: str | None) -> dict[str, str]:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    referer = "https://bankr.bot/"
    if "/llm" in parsed.path:
        referer = "https://bankr.bot/llm"
    elif origin == "https://bankr.bot":
        referer = "https://bankr.bot/terminal"

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://bankr.bot",
        "Referer": referer,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    }
    if session_cookie:
        headers["Cookie"] = session_cookie
    return headers


def parse_html_snapshot(html: str, text_limit: int = 2500, link_limit: int = 40) -> dict[str, Any]:
    clean = re.sub(r"<script[\\s\\S]*?</script>", " ", html, flags=re.IGNORECASE)
    clean = re.sub(r"<style[\\s\\S]*?</style>", " ", clean, flags=re.IGNORECASE)

    title_match = re.search(r"<title[^>]*>([\\s\\S]*?)</title>", clean, flags=re.IGNORECASE)
    title = unescape(title_match.group(1).strip()) if title_match else ""

    heading_matches = re.findall(r"<(h1|h2|h3)[^>]*>([\\s\\S]*?)</\\1>", clean, flags=re.IGNORECASE)
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


def mask_key(key: str | None) -> str:
    if not key:
        return ""
    if len(key) <= 12:
        return "[masked]"
    return f"{key[:8]}...{key[-4:]}"


def get_agent_status(bankr_api_key: str | None) -> dict[str, Any]:
    if not bankr_api_key:
        return {
            "available": False,
            "reason": "BANKR_API_KEY not set",
            "auth_ok": False,
        }

    headers = {"X-API-Key": bankr_api_key, "Content-Type": "application/json"}
    result = safe_request(BANKR_AGENT_ME_URL, headers=headers)
    return {
        "available": True,
        "auth_ok": result.get("status_code") == 200,
        "key_mask": mask_key(bankr_api_key),
        "status_code": result.get("status_code"),
        "data": result.get("json") or {},
        "error": (result.get("json") or {}).get("error") if result.get("json") else result.get("error"),
    }


def get_llm_usage(bankr_llm_key: str | None) -> dict[str, Any]:
    if not bankr_llm_key:
        return {
            "available": False,
            "reason": "BANKR_LLM_KEY not set",
            "auth_ok": False,
        }

    headers = {"X-API-Key": bankr_llm_key, "Content-Type": "application/json"}
    first = safe_request(BANKR_LLM_USAGE_URL, headers=headers)

    if first.get("status_code") == 200:
        return {
            "available": True,
            "auth_ok": True,
            "method": "X-API-Key",
            "key_mask": mask_key(bankr_llm_key),
            "status_code": 200,
            "data": first.get("json") or {},
        }

    headers_bearer = {"Authorization": f"Bearer {bankr_llm_key}", "Content-Type": "application/json"}
    second = safe_request(BANKR_LLM_USAGE_URL, headers=headers_bearer)

    return {
        "available": True,
        "auth_ok": second.get("status_code") == 200,
        "method": "Bearer",
        "key_mask": mask_key(bankr_llm_key),
        "status_code": second.get("status_code"),
        "data": second.get("json") or {},
        "error": (second.get("json") or {}).get("error") if second.get("json") else second.get("error"),
    }


def summarize_json_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        summary: dict[str, Any] = {
            "type": "object",
            "top_level_keys": list(payload.keys())[:25],
        }
        for key in [
            "id",
            "wallet",
            "walletAddress",
            "address",
            "model",
            "provider",
            "totalEarned",
            "totalEarnedFormatted",
            "claimable",
            "claimableFormatted",
            "count",
            "total",
            "days",
        ]:
            if key in payload:
                summary[key] = payload.get(key)

        array_counts: dict[str, int] = {}
        for key, value in payload.items():
            if isinstance(value, list):
                array_counts[key] = len(value)
        if array_counts:
            summary["array_counts"] = array_counts

        return summary

    if isinstance(payload, list):
        summary = {
            "type": "array",
            "length": len(payload),
        }
        if payload:
            first = payload[0]
            if isinstance(first, dict):
                summary["first_item_keys"] = list(first.keys())[:20]
        return summary

    return {
        "type": type(payload).__name__,
        "value": payload,
    }


def get_browser_api_data(session_cookie: str | None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for name, url in BANKR_BROWSER_API_ENDPOINTS:
        page = safe_request(url, headers=build_browser_headers(url, session_cookie))
        payload = page.get("json")
        results.append(
            {
                "name": name,
                "url": url,
                "status_code": page.get("status_code"),
                "ok": page.get("ok"),
                "content_type": page.get("content_type"),
                "summary": summarize_json_payload(payload) if payload is not None else None,
                "data": payload,
                "error": (payload or {}).get("error") if isinstance(payload, dict) else page.get("error"),
                "text_excerpt": (page.get("text") or "")[:500],
            }
        )

    return results


def get_web_tab_snapshots(session_cookie: str | None, text_limit: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for url in BANKR_WEB_TABS:
        page = safe_request(url, headers=build_browser_headers(url, session_cookie))
        snap = parse_html_snapshot(page.get("text", ""), text_limit=text_limit)
        results.append(
            {
                "url": url,
                "status_code": page.get("status_code"),
                "ok": page.get("ok"),
                "content_type": page.get("content_type"),
                "snapshot": snap,
            }
        )
    return results


def get_local_miner_status(bankr_api_key: str | None) -> dict[str, Any]:
    if not bankr_api_key:
        return {"available": False, "reason": "BANKR_API_KEY not set"}

    try:
        from litcoin import Agent

        agent = Agent(bankr_key=bankr_api_key)
        status = agent.status()
        return {
            "available": True,
            "ok": True,
            "status": status,
        }
    except Exception as exc:
        return {
            "available": True,
            "ok": False,
            "error": str(exc),
        }


def build_markdown(report: dict[str, Any]) -> str:
    agent = report.get("bankr_agent", {})
    llm = report.get("bankr_llm", {})
    local = report.get("local_miner", {})
    browser_api = report.get("browser_api", [])

    lines: list[str] = []
    lines.append("# Bankr Mirror Report")
    lines.append("")
    lines.append(f"- Generated: {report.get('generated_at_utc', '')}")
    lines.append(f"- Agent Auth: {'OK' if agent.get('auth_ok') else 'FAILED'}")
    lines.append(f"- LLM Auth: {'OK' if llm.get('auth_ok') else 'FAILED'}")
    lines.append(f"- Browser Cookie Mode: {'ON' if report.get('notes', {}).get('has_session_cookie') else 'OFF'}")
    expiry = report.get('notes', {}).get('privy_token_expiry', {})
    if expiry.get('found'):
        if expiry.get('expired'):
            lines.append("- Session Token: **EXPIRED — paste fresh cookie to vault**")
        else:
            lines.append(f"- Session Token: valid for {expiry.get('minutes_remaining')} min (expires {expiry.get('expires_utc')})")
    lines.append("")

    lines.append("## Agent API")
    lines.append(f"- Key: {agent.get('key_mask', '')}")
    lines.append(f"- HTTP: {agent.get('status_code', 'n/a')}")
    a = agent.get("data") or {}
    if a:
        wallets = a.get("wallets") or []
        evm = next((w.get("address") for w in wallets if isinstance(w, dict) and w.get("chain") == "evm"), None)
        lines.append(f"- EVM Wallet: {evm or 'n/a'}")
        lines.append(f"- Total Earned: {a.get('totalEarnedFormatted', a.get('totalEarned', 'n/a'))}")
        lines.append(f"- Claimable: {a.get('claimableFormatted', a.get('claimable', 'n/a'))}")

    lines.append("")
    lines.append("## LLM Gateway")
    lines.append(f"- Key: {llm.get('key_mask', '')}")
    lines.append(f"- Method: {llm.get('method', 'n/a')}")
    lines.append(f"- HTTP: {llm.get('status_code', 'n/a')}")
    if llm.get("error"):
        lines.append(f"- Error: {llm.get('error')}")
    if llm.get("data"):
        lines.append("- Data present: yes")

    lines.append("")
    lines.append("## Local Miner Status")
    lines.append(f"- SDK status fetch: {'OK' if local.get('ok') else 'FAILED'}")
    s = (local.get("status") or {}) if local.get("ok") else {}
    if s:
        lines.append(f"- Total Earned: {s.get('totalEarnedFormatted', s.get('totalEarned', 'n/a'))}")
        lines.append(f"- Claimable: {s.get('claimableFormatted', s.get('claimable', 'n/a'))}")

    lines.append("")
    lines.append("## Browser API")
    for item in browser_api:
        summary = item.get("summary") or {}
        lines.append(f"- {item.get('name')}: HTTP {item.get('status_code')} ok={item.get('ok')}")
        if summary.get("top_level_keys"):
            lines.append(f"  keys: {', '.join(summary.get('top_level_keys', []))}")
        if summary.get("length") is not None:
            lines.append(f"  items: {summary.get('length')}")
        if summary.get("array_counts"):
            counts = ", ".join(f"{key}={value}" for key, value in summary.get("array_counts", {}).items())
            lines.append(f"  arrays: {counts}")
        if item.get("error"):
            lines.append(f"  error: {item.get('error')}")

    lines.append("")
    lines.append("## Bankr Web Tabs")
    for tab in report.get("web_tabs", []):
        lines.append(f"- {tab.get('url')}: HTTP {tab.get('status_code')} title={((tab.get('snapshot') or {}).get('title') or 'n/a')}")

    lines.append("")
    lines.append("## Alignment Check")
    lines.append("- Agent API key and LLM gateway key are separate credentials.")
    lines.append("- If LITCOIN miner shows one model while LLM page shows another, that is expected unless relay mode is enabled with AI key.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Mirror Bankr API + web tabs + local miner status")
    parser.add_argument("--out-dir", default="reports", help="Output directory")
    parser.add_argument("--text-limit", type=int, default=1800, help="Visible text excerpt length")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    bankr_api_key = os.getenv("BANKR_API_KEY") or os.getenv("BANKR_KEY")
    bankr_llm_key = os.getenv("BANKR_LLM_KEY")
    session_cookie = os.getenv("BANKR_SESSION_COOKIE")

    token_expiry = parse_privy_token_expiry(session_cookie)
    report = {
        "generated_at_utc": now_utc(),
        "bankr_agent": get_agent_status(bankr_api_key),
        "bankr_llm": get_llm_usage(bankr_llm_key),
        "local_miner": get_local_miner_status(bankr_api_key),
        "browser_api": get_browser_api_data(session_cookie),
        "web_tabs": get_web_tab_snapshots(session_cookie, text_limit=args.text_limit),
        "notes": {
            "has_session_cookie": bool(session_cookie),
            "has_llm_key": bool(bankr_llm_key),
            "browser_api_sources": [name for name, _ in BANKR_BROWSER_API_ENDPOINTS],
            "privy_token_expiry": token_expiry,
        },
    }

    json_path = out_dir / f"bankr_mirror_{stamp}.json"
    md_path = out_dir / f"bankr_mirror_{stamp}.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(build_markdown(report))

    print(f"Report JSON: {json_path}")
    print(f"Report MD:   {md_path}")
    print(f"AgentAuth:   {report['bankr_agent'].get('auth_ok')}")
    print(f"LLMAuth:     {report['bankr_llm'].get('auth_ok')}")
    print(f"CookieMode:  {report['notes']['has_session_cookie']}")
    expiry = report['notes']['privy_token_expiry']
    if expiry.get('found'):
        if expiry.get('expired'):
            print("SessionToken: EXPIRED")
        else:
            print(f"SessionToken: valid {expiry.get('minutes_remaining')} min")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
