#!/usr/bin/env python3
"""Fetch Base token lists and export symbol/address pairs.

Usage:
  python scripts/pull_tokenlists.py
  python scripts/pull_tokenlists.py --out data/base_tokenlist.csv
  python scripts/pull_tokenlists.py --update-allowlist
"""

import argparse
import json
import os
import pathlib
import requests

TOKENLIST_URLS = [
    "https://tokens.uniswap.org",
    "https://token-list.sushi.com",
    "https://static.optimism.io/optimism.tokenlist.json",
]

BASE_CHAIN_ID = 8453

BASESCAN_API_ACTIONS = [
    "tokenlist",
]


def fetch_tokens(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            data = r.json()
            return data.get("tokens", [])
        except Exception as e:
            if i == retries - 1:
                print(f"Failed to fetch {url}: {e}")
            continue
    return []


def fetch_basescan_tokens():
    api_url = os.getenv("EXPLORER_API_URL", "https://api.basescan.org/api")
    api_key = os.getenv("EXPLORER_API_KEY", "")
    if not api_key:
        return []

    for action in BASESCAN_API_ACTIONS:
        params = {
            "module": "token",
            "action": action,
            "apikey": api_key,
        }
        try:
            r = requests.get(api_url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            if str(data.get("status")) != "1":
                continue
            result = data.get("result")
            if isinstance(result, list):
                return result
        except Exception as e:
            print(f"Failed to fetch BaseScan ({action}): {e}")
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Base tokenlists")
    parser.add_argument("--out", type=str, default="data/base_tokenlist.csv")
    parser.add_argument("--update-allowlist", action="store_true")
    args = parser.parse_args()

    base_dir = pathlib.Path(__file__).resolve().parents[1]
    out_path = base_dir / args.out

    seen = set()
    rows = []

    for url in TOKENLIST_URLS:
        for t in fetch_tokens(url):
            try:
                if int(t.get("chainId", 0)) != BASE_CHAIN_ID:
                    continue
            except Exception:
                continue
            symbol = str(t.get("symbol", "")).upper().strip()
            address = t.get("address")
            if not symbol or not address:
                continue
            key = (symbol, address)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"symbol": symbol, "address": address})

    for t in fetch_basescan_tokens():
        symbol = str(t.get("symbol", "")).upper().strip()
        address = t.get("address") or t.get("contractAddress")
        if not symbol or not address:
            continue
        key = (symbol, address)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"symbol": symbol, "address": address})

    os.makedirs(out_path.parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("symbol,address\n")
        for r in rows:
            f.write(f"{r['symbol']},{r['address']}\n")

    print(f"Wrote {len(rows)} rows to {out_path}")

    if args.update_allowlist:
        allowlist_path = base_dir / "data" / "allowlist.json"
        existing = []
        if allowlist_path.exists():
            try:
                with open(allowlist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and isinstance(data.get("tokens"), list):
                    existing = data.get("tokens")
                elif isinstance(data, list):
                    existing = data
            except Exception:
                existing = []

        merged = list(existing)
        for r in rows:
            merged.append({"symbol": r["symbol"], "address": r["address"]})

        with open(allowlist_path, "w", encoding="utf-8") as f:
            json.dump({"tokens": merged}, f, indent=2)
        print(f"Updated allowlist: {allowlist_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
