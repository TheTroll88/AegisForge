#!/usr/bin/env python3
"""Filter allowlist to tokens with an on-chain pool against a quote token.

Usage:
  python scripts/filter_allowlist_pools.py
  python scripts/filter_allowlist_pools.py --quote USDC --inplace
"""

import argparse
import json
import os
import pathlib
import sys
from typing import List, Dict, Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.dex_trader import DEXTrader
from core.wallet_manager import WalletManager


def _load_allowlist(path: pathlib.Path) -> List[Any]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and isinstance(data.get("tokens"), list):
        return data.get("tokens")
    if isinstance(data, list):
        return data
    return []


def _write_allowlist(path: pathlib.Path, tokens: List[Dict[str, str]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"tokens": tokens}, f, indent=2)


def _token_id(entry: Any) -> str:
    if isinstance(entry, dict):
        sym = entry.get("symbol")
        addr = entry.get("address")
        if sym:
            return str(sym).upper()
        if addr:
            return str(addr)
    return str(entry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter allowlist by pool availability")
    parser.add_argument("--quote", type=str, default=os.getenv("DEFAULT_QUOTE_TOKEN", "USDC"))
    parser.add_argument("--inplace", action="store_true")
    args = parser.parse_args()

    base_dir = pathlib.Path(__file__).resolve().parents[1]
    allowlist_path = base_dir / "data" / "allowlist.json"
    out_path = base_dir / "data" / "allowlist_filtered.json"

    wallet = WalletManager()
    dex = DEXTrader(wallet)

    quote = args.quote.strip()
    quote_addr, quote_is_native = dex.resolve_token(quote)
    if quote_is_native:
        quote_addr = dex._checksum(dex.tokens.get("WETH"))
    if not quote_addr:
        print(f"Failed to resolve quote token: {quote}")
        return 1

    tokens = _load_allowlist(allowlist_path)
    if not tokens:
        print("Allowlist is empty.")
        return 1

    filtered: List[Dict[str, str]] = []
    for entry in tokens:
        token_id = _token_id(entry)
        addr, is_native = dex.resolve_token(token_id)
        if is_native:
            addr = dex._checksum(dex.tokens.get("WETH"))
        if not addr:
            continue

        fee = dex._select_fee(addr, quote_addr)
        if fee is None:
            continue

        if isinstance(entry, dict) and entry.get("symbol"):
            filtered.append({"symbol": str(entry.get("symbol")).upper(), "address": addr})
        else:
            filtered.append({"symbol": addr, "address": addr})

    # De-duplicate by address
    seen = set()
    deduped = []
    for t in filtered:
        addr = t.get("address")
        if addr and addr not in seen:
            seen.add(addr)
            deduped.append(t)

    target = allowlist_path if args.inplace else out_path
    _write_allowlist(target, deduped)

    print(f"Filtered tokens: {len(deduped)}")
    print(f"Wrote: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
