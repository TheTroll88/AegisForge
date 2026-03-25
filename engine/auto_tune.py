"""
AegisForge Strategy Auto-Tuner
Reads the latest backtest report and computes performance-weighted strategy weights.
Run standalone: cd engine && python auto_tune.py
"""

import glob
import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
WEIGHTS_PATH = DATA_DIR / "strategy_weights.json"

# Map backtest class names to short weight keys
CLASS_TO_KEY = {
    "RSIStrategy": "rsi",
    "MomentumStrategy": "momentum",
    "MACDStrategy": "macd",
    "BollingerStrategy": "bollinger",
    "BreakoutStrategy": "breakout",
    "VolumeSpikeStrategy": "volume_spike",
    "AegisFusionStrategy": "aegis_fusion",
    "RSITrendStrategy": "rsi_trend",
}

MIN_WEIGHT = 0.05


def find_latest_backtest() -> Path | None:
    pattern = str(LOGS_DIR / "backtest_*.json")
    files = sorted(glob.glob(pattern))
    return Path(files[-1]) if files else None


def compute_weights(report: dict) -> dict:
    """Compute normalized strategy weights from a backtest report dict."""
    strats = report.get("strategies", {})
    if not strats:
        return {}

    max_trades = max((s.get("total_trades", 0) for s in strats.values()), default=1) or 1

    raw_scores = {}
    for class_name, metrics in strats.items():
        key = CLASS_TO_KEY.get(class_name, class_name.lower().replace("strategy", "").strip("_"))
        roi = metrics.get("roi_pct", 0)
        wr = metrics.get("win_rate", 0)
        trades = metrics.get("total_trades", 0)

        score = (roi * 0.4) + (wr * 0.4) + ((trades / max_trades) * 100 * 0.2)
        raw_scores[key] = score

    # Assign minimum weight to negative-ROI strategies, then normalize
    weights = {}
    negative_keys = [k for k, s in raw_scores.items() if s <= 0]
    positive_keys = [k for k, s in raw_scores.items() if s > 0]

    # Reserve budget for minimum-weight strategies
    reserved = len(negative_keys) * MIN_WEIGHT
    remaining_budget = 1.0 - reserved

    if positive_keys:
        positive_total = sum(raw_scores[k] for k in positive_keys)
        for k in positive_keys:
            weights[k] = max(MIN_WEIGHT, (raw_scores[k] / positive_total) * remaining_budget)
    for k in negative_keys:
        weights[k] = MIN_WEIGHT

    # Final normalization to ensure sum == 1.0
    total = sum(weights.values())
    if total > 0:
        weights = {k: round(v / total, 4) for k, v in weights.items()}

    return weights


def load_current_weights() -> dict:
    if WEIGHTS_PATH.exists():
        with open(WEIGHTS_PATH, "r") as f:
            data = json.load(f)
        return data.get("weights", {})
    return {}


def save_weights(weights: dict, source_file: str) -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "source_report": source_file,
        "weights": weights,
    }
    with open(WEIGHTS_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    return payload


def print_summary(old_weights: dict, new_weights: dict):
    all_keys = sorted(set(list(old_weights.keys()) + list(new_weights.keys())))
    print(f"\n{'Strategy':<20} {'Old':>8} {'New':>8} {'Change':>8}")
    print("-" * 46)
    for k in all_keys:
        old = old_weights.get(k, 0)
        new = new_weights.get(k, 0)
        diff = new - old
        sign = "+" if diff > 0 else ""
        print(f"{k:<20} {old:>8.4f} {new:>8.4f} {sign}{diff:>7.4f}")
    print(f"\nTotal: {sum(new_weights.values()):.4f}")


def run():
    report_path = find_latest_backtest()
    if not report_path:
        print("No backtest reports found in logs/")
        return None

    with open(report_path, "r") as f:
        report = json.load(f)

    print(f"Source: {report_path.name}")
    old_weights = load_current_weights()
    new_weights = compute_weights(report)

    if not new_weights:
        print("No strategies found in report.")
        return None

    save_weights(new_weights, report_path.name)
    print_summary(old_weights, new_weights)
    return new_weights


if __name__ == "__main__":
    run()
