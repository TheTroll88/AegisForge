#!/usr/bin/env python3
"""Check transaction receipt status for a list of tx hashes.

Usage:
  python scripts/check_tx_receipts.py <hash1> <hash2> ...

If no hashes are provided, the script will read from:
  engine/data/approved_tx_hashes.txt
"""

import os
import sys
import pathlib
from typing import List

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.wallet_manager import WalletManager


def _load_hashes_from_file(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    hashes = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            h = line.strip()
            if not h or h.startswith("#"):
                continue
            hashes.append(h)
    return hashes


def _normalize_hash(h: str) -> str:
    h = h.strip()
    if not h:
        return h
    return h if h.startswith("0x") else f"0x{h}"


def main() -> int:
    input_hashes = [_normalize_hash(h) for h in sys.argv[1:] if h.strip()]

    if not input_hashes:
        default_path = os.path.join(
            pathlib.Path(__file__).resolve().parents[1],
            "data",
            "approved_tx_hashes.txt",
        )
        input_hashes = _load_hashes_from_file(default_path)

    if not input_hashes:
        print("No tx hashes provided.")
        return 1

    wallet = WalletManager()
    w3 = wallet.w3

    ok = 0
    failed = 0
    pending = 0
    errored = 0

    for h in input_hashes:
        try:
            receipt = w3.eth.get_transaction_receipt(h)
            status = receipt.get("status")
            if status == 1:
                ok += 1
                print(f"OK      {h}")
            else:
                failed += 1
                print(f"FAIL    {h}")
        except Exception as e:
            msg = str(e).lower()
            if "not found" in msg or "unknown transaction" in msg:
                pending += 1
                print(f"PENDING {h}")
            else:
                errored += 1
                print(f"ERROR   {h} ({e})")

    print(
        f"\nSummary: ok={ok} fail={failed} pending={pending} error={errored}"
    )
    return 0 if failed == 0 and errored == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
