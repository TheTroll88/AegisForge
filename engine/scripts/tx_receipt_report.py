#!/usr/bin/env python3
"""Generate a simple report from tx_receipts.json.

Usage:
  python scripts/tx_receipt_report.py
  python scripts/tx_receipt_report.py --limit 50
  python scripts/tx_receipt_report.py --out logs/tx_receipt_report.csv
"""

import argparse
import json
import os
import pathlib
from datetime import datetime
from typing import List, Dict, Any


def _load_receipts(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            data = json.load(f)
        except Exception:
            return []
    return data if isinstance(data, list) else []


def _status_counts(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"confirmed": 0, "reverted": 0, "error": 0}
    for r in rows:
        status = str(r.get("status", "")).lower()
        if status in counts:
            counts[status] += 1
    return counts


def _write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    import csv

    fields = [
        "timestamp",
        "tx_hash",
        "status",
        "block_number",
        "gas_used",
        "effective_gas_price",
        "receipt_status",
        "error",
    ]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate tx receipt report")
    parser.add_argument("--limit", type=int, default=50, help="number of recent records to show")
    parser.add_argument("--out", type=str, default="", help="optional CSV output path")
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

    counts = _status_counts(rows)
    total = len(rows)
    print(f"Total: {total} | confirmed: {counts['confirmed']} | reverted: {counts['reverted']} | error: {counts['error']}")

    recent = rows[-args.limit :]
    print("\nMost recent:")
    for r in recent:
        ts = r.get("timestamp", "")
        status = r.get("status", "")
        txh = r.get("tx_hash", "")
        block = r.get("block_number", "")
        line = f"{ts} | {status:9} | {txh} | block={block}"
        print(line)

    if args.out:
        out_path = args.out
    else:
        out_path = os.path.join(base_dir, "logs", "tx_receipt_report.csv")

    _write_csv(out_path, rows)
    print(f"\nCSV report written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
