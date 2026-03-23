#!/usr/bin/env python3
"""Run test_micro_trader for a fixed duration, then generate receipt report.

Usage:
  python scripts/run_test_loop.py --minutes 5
"""

import argparse
import subprocess
import sys
import time
import pathlib


def main() -> int:
    parser = argparse.ArgumentParser(description="Run test_micro_trader for a fixed duration")
    parser.add_argument("--minutes", type=int, default=5, help="run duration in minutes")
    args = parser.parse_args()

    base_dir = pathlib.Path(__file__).resolve().parents[1]
    test_path = base_dir / "test_micro_trader.py"
    report_path = base_dir / "scripts" / "tx_receipt_report.py"

    duration = max(1, args.minutes) * 60
    print(f"Starting test_micro_trader for {args.minutes} minute(s)...")

    proc = subprocess.Popen([sys.executable, str(test_path)])
    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        print("Interrupted; stopping test...")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    print("\nGenerating receipt report...")
    subprocess.run([sys.executable, str(report_path), "--limit", "50"], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
