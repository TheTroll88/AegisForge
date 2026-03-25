"""
AegisForge Backtester
Runs all strategies against synthetic or historical price data.
Produces per-strategy and aggregate performance reports.

Usage:
    cd engine
    python backtest.py                     # synthetic data, all strategies
    python backtest.py --days 60           # 60-day synthetic run
    python backtest.py --csv data/eth.csv  # historical CSV (columns: timestamp,price)
"""

import argparse
import csv
import importlib
import json
import logging
import math
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ---------- synthetic price generator ----------

def generate_synthetic_prices(days=30, interval_seconds=60, base_price=2000.0, volatility=0.02):
    """Generate realistic-ish crypto price series with trends, mean-reversion, and spikes."""
    points = int(days * 86400 / interval_seconds)
    prices = []
    price = base_price
    trend = 0.0
    start = datetime.now(tz=None) - timedelta(days=days)

    for i in range(points):
        # Random walk + slow trend drift + occasional spike
        trend += random.gauss(0, 0.0001)
        trend = max(-0.001, min(0.001, trend))
        change = random.gauss(trend, volatility / math.sqrt(86400 / interval_seconds))

        # Occasional whale spike (0.3 % chance per candle)
        if random.random() < 0.003:
            change += random.choice([-1, 1]) * random.uniform(0.01, 0.04)

        price *= (1 + change)
        price = max(price * 0.5, price)  # floor at 50 % of current

        ts = start + timedelta(seconds=i * interval_seconds)
        prices.append({
            "timestamp": ts.isoformat(),
            "price": round(price, 4),
            "symbol": "ETH/USD",
            "volume": round(random.uniform(100, 5000), 2),
        })

    return prices


def load_csv_prices(csv_path):
    """Load price data from CSV. Expected columns: timestamp, price.  Optional: symbol, volume."""
    prices = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prices.append({
                "timestamp": row.get("timestamp", ""),
                "price": float(row["price"]),
                "symbol": row.get("symbol", "ETH/USD"),
                "volume": float(row.get("volume", 0)),
            })
    return prices


# ---------- strategy loader ----------

def load_all_strategies(strategies_dir: Path):
    """Dynamically load all *_strategy.py files from the strategies directory."""
    strats = []
    if not strategies_dir.exists():
        return strats
    for f in sorted(strategies_dir.iterdir()):
        if f.suffix == ".py" and f.name != "__init__.py":
            module_name = f.stem
            try:
                mod = importlib.import_module(f"strategies.{module_name}")
                # Find *Strategy class
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, type) and attr_name.endswith("Strategy"):
                        strats.append((attr_name, attr()))
                        break
            except Exception as e:
                logging.warning(f"Skip {module_name}: {e}")
    return strats


# ---------- backtest runner ----------

class BacktestTrader:
    """Lightweight paper trader for backtesting — tracks per-strategy P&L."""

    def __init__(self, starting_balance=10000.0):
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.position = None
        self.entry_price = None
        self.trades = []
        self.wins = 0
        self.losses = 0

    def execute(self, signal, market_data, strategy_name="unknown"):
        action = signal.get("action", "hold")
        price = market_data.get("price", 0)
        if action == "buy" and self.position is None:
            self.position = "long"
            self.entry_price = price
            self.trades.append({"action": "buy", "price": price, "ts": market_data.get("timestamp"), "strategy": strategy_name})
        elif action == "sell" and self.position == "long" and self.entry_price:
            profit = price - self.entry_price
            roi = (profit / self.entry_price) * 100
            result = "win" if profit > 0 else "loss"
            if profit > 0:
                self.wins += 1
            else:
                self.losses += 1
            self.balance += profit
            self.trades.append({
                "action": "sell", "price": price, "ts": market_data.get("timestamp"),
                "strategy": strategy_name, "profit": round(profit, 4), "roi": round(roi, 2), "result": result,
            })
            self.position = None
            self.entry_price = None

    def summary(self):
        total = self.wins + self.losses
        win_rate = (self.wins / total * 100) if total else 0
        net = round(self.balance - self.starting_balance, 2)
        return {
            "total_trades": total,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": round(win_rate, 1),
            "net_pnl": net,
            "final_balance": round(self.balance, 2),
            "roi_pct": round((net / self.starting_balance) * 100, 2),
        }


def run_backtest(prices, strategies, starting_balance=10000.0):
    """Run each strategy independently against the same price series."""
    results = {}
    for name, strategy in strategies:
        trader = BacktestTrader(starting_balance)
        for data_point in prices:
            try:
                signal = strategy.evaluate(data_point)
                trader.execute(signal, data_point, strategy_name=name)
            except Exception:
                pass
        results[name] = {**trader.summary(), "trade_log": trader.trades}

    return results


# ---------- reporting ----------

def print_report(results, prices):
    start_price = prices[0]["price"]
    end_price = prices[-1]["price"]
    buy_hold_roi = round(((end_price - start_price) / start_price) * 100, 2)
    duration_hrs = len(prices) / 60  # assuming 1-min candles

    print("\n" + "=" * 70)
    print(f"  AEGISFORGE BACKTEST REPORT")
    print(f"  {len(prices):,} candles | {duration_hrs:.0f} hours | {prices[0]['symbol']}")
    print(f"  Price: ${start_price:,.2f} → ${end_price:,.2f}  (Buy & Hold: {buy_hold_roi}%)")
    print("=" * 70)

    header = f"{'Strategy':<28} {'Trades':>7} {'Win%':>6} {'Net P&L':>10} {'ROI%':>7}"
    print(header)
    print("-" * 70)

    for name, data in sorted(results.items(), key=lambda x: x[1]["net_pnl"], reverse=True):
        beat = "✓" if data["roi_pct"] > buy_hold_roi else " "
        print(f"  {name:<26} {data['total_trades']:>7} {data['win_rate']:>5.1f}% ${data['net_pnl']:>9,.2f} {data['roi_pct']:>6.1f}% {beat}")

    print("-" * 70)

    best = max(results.items(), key=lambda x: x[1]["net_pnl"])
    worst = min(results.items(), key=lambda x: x[1]["net_pnl"])
    print(f"  Best:  {best[0]} (+${best[1]['net_pnl']:,.2f})")
    print(f"  Worst: {worst[0]} (${worst[1]['net_pnl']:,.2f})")
    print(f"  Buy & Hold benchmark: {buy_hold_roi}%")
    print("=" * 70 + "\n")


def save_report(results, prices, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary = {}
    for name, data in results.items():
        summary[name] = {k: v for k, v in data.items() if k != "trade_log"}

    summary_path = os.path.join(output_dir, f"backtest_{ts}.json")
    with open(summary_path, "w") as f:
        json.dump({
            "timestamp": ts,
            "candles": len(prices),
            "symbol": prices[0]["symbol"],
            "start_price": prices[0]["price"],
            "end_price": prices[-1]["price"],
            "strategies": summary,
        }, f, indent=2)
    print(f"Report saved: {summary_path}")


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description="AegisForge Strategy Backtester")
    parser.add_argument("--days", type=int, default=30, help="Days of synthetic data (default: 30)")
    parser.add_argument("--csv", type=str, help="Path to historical price CSV")
    parser.add_argument("--balance", type=float, default=10000, help="Starting balance (default: 10000)")
    parser.add_argument("--save", action="store_true", help="Save JSON report to logs/")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    if args.csv:
        print(f"Loading prices from {args.csv}...")
        prices = load_csv_prices(args.csv)
    else:
        print(f"Generating {args.days}-day synthetic price data...")
        prices = generate_synthetic_prices(days=args.days)

    print(f"Loaded {len(prices):,} candles")

    strategies_dir = Path(__file__).resolve().parent / "strategies"
    strategies = load_all_strategies(strategies_dir)
    print(f"Loaded {len(strategies)} strategies: {', '.join(n for n, _ in strategies)}")

    if not strategies:
        print("No strategies found. Exiting.")
        sys.exit(1)

    results = run_backtest(prices, strategies, starting_balance=args.balance)
    print_report(results, prices)

    if args.save:
        save_report(results, prices, str(Path(__file__).resolve().parent / "logs"))


if __name__ == "__main__":
    main()
