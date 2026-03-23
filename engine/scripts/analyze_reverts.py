#!/usr/bin/env python3
"""Analyze reverted txs and try to decode revert reasons.

Usage:
  python scripts/analyze_reverts.py --limit 20
  python scripts/analyze_reverts.py --hash 0xabc...
"""

import argparse
import json
import os
import pathlib
from typing import List, Dict, Any, Optional

from eth_abi import decode
from web3 import Web3

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.wallet_manager import WalletManager


ERROR_SIG = "0x08c379a0"  # Error(string)
PANIC_SIG = "0x4e487b71"  # Panic(uint256)


def _load_receipts(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            data = json.load(f)
        except Exception:
            return []
    return data if isinstance(data, list) else []


def _decode_revert_data(data_hex: str) -> Optional[str]:
    if not data_hex or not data_hex.startswith("0x"):
        return None
    if data_hex.startswith(ERROR_SIG):
        try:
            raw = bytes.fromhex(data_hex[10:])
            reason = decode(["string"], raw)[0]
            return f"Error({reason})"
        except Exception:
            return None
    if data_hex.startswith(PANIC_SIG):
        try:
            raw = bytes.fromhex(data_hex[10:])
            code = decode(["uint256"], raw)[0]
            return f"Panic(0x{int(code):x})"
        except Exception:
            return None
    return None


def _call_with_revert_reason(w3: Web3, tx: Dict[str, Any]) -> Optional[str]:
    call_tx = {
        "to": tx.get("to"),
        "from": tx.get("from"),
        "data": tx.get("input"),
        "value": tx.get("value"),
    }
    try:
        w3.eth.call(call_tx, block_identifier=tx.get("blockNumber"))
        return None
    except Exception as e:
        # Try to parse revert data from the exception
        msg = str(e)
        if "execution reverted" in msg and "0x" in msg:
            data_hex = msg[msg.find("0x"):].split(" ")[0].strip()
            decoded = _decode_revert_data(data_hex)
            return decoded or f"execution reverted ({data_hex[:66]})"
        return msg


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze reverted txs")
    parser.add_argument("--limit", type=int, default=20, help="number of recent reverts to analyze")
    parser.add_argument("--hash", type=str, default="", help="single tx hash to analyze")
    args = parser.parse_args()

    base_dir = pathlib.Path(__file__).resolve().parents[1]
    receipt_log = os.getenv(
        "TX_RECEIPT_LOG_FILE",
        os.path.join(base_dir, "logs", "tx_receipts.json"),
    )

    rows = _load_receipts(receipt_log)
    if not rows:
        print("No receipt records found.")
        return 1

    hashes: List[str] = []
    if args.hash:
        hashes = [args.hash]
    else:
        for r in reversed(rows):
            if str(r.get("status", "")) == "reverted":
                hashes.append(r.get("tx_hash"))
                if len(hashes) >= args.limit:
                    break

    if not hashes:
        print("No reverted txs found.")
        return 0

    wallet = WalletManager()
    w3 = wallet.w3

    for h in hashes:
        if not h:
            continue
        if not h.startswith("0x"):
            h = f"0x{h}"
        try:
            tx = w3.eth.get_transaction(h)
        except Exception as e:
            print(f"{h} | unable to fetch tx ({e})")
            continue

        reason = _call_with_revert_reason(w3, tx)
        if reason:
            print(f"{h} | {reason}")
        else:
            print(f"{h} | no revert reason returned")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
