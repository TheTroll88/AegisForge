import os
import csv
import json
from datetime import datetime

class TradeLogger:
    def __init__(self):
        base_path = r"C:\Users\natha\Dev\The_Birth_of_a_Pantheon_PhasePort\The_Birth_of_a_Pantheon_PhasePort\kratos_core\logs"

        self.csv_file = os.path.join(base_path, "trade_history.csv")
        self.json_file = os.path.join(base_path, "trade_log.json")
        self.performance_file = os.path.join(base_path, "performance.json")

        os.makedirs(base_path, exist_ok=True)

        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "symbol", "action", "price", "result", "roi", "profit"])
                writer.writeheader()

        if not os.path.exists(self.json_file):
            with open(self.json_file, mode='w') as f:
                json.dump([], f)

        if not os.path.exists(self.performance_file):
            with open(self.performance_file, mode='w') as f:
                json.dump({}, f)

    def log(self, trade):
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        csv_data = {
            "timestamp": timestamp,
            "symbol": trade.get("symbol", "UNKNOWN"),
            "action": trade.get("action", "UNKNOWN"),
            "price": trade.get("price", 0),
            "result": trade.get("result", ""),
            "roi": trade.get("roi", ""),
            "profit": trade.get("profit", "")
        }

        # Write to CSV
        with open(self.csv_file, mode='a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_data.keys())
            writer.writerow(csv_data)

        # Write to JSON log
        with open(self.json_file, mode='r+') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append({**csv_data, "timestamp": timestamp})
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        # Update performance
        if csv_data["result"] in ["win", "loss"]:
            self._update_performance(csv_data)

    def _update_performance(self, trade):
        symbol = trade["symbol"]
        result = trade["result"]
        roi = float(trade["roi"]) if trade["roi"] else 0
        profit = float(trade["profit"]) if trade["profit"] else 0

        with open(self.performance_file, mode='r+') as f:
            try:
                performance = json.load(f)
            except json.JSONDecodeError:
                performance = {}

            if symbol not in performance:
                performance[symbol] = {
                    "wins": 0,
                    "losses": 0,
                    "total_trades": 0,
                    "total_profit": 0.0,
                    "avg_roi": 0.0
                }

            stats = performance[symbol]
            stats["total_trades"] += 1
            if result == "win":
                stats["wins"] += 1
            elif result == "loss":
                stats["losses"] += 1
            stats["total_profit"] += profit

            # Recalculate average ROI
            if stats["total_trades"] > 0:
                stats["avg_roi"] = round(stats["total_profit"] / stats["total_trades"], 2)

            f.seek(0)
            json.dump(performance, f, indent=2)
            f.truncate()

    def log_simple(self, trade_record):
        """Simple logging for trade signals"""
        try:
            with open(self.json_file, mode='r+') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                data.append(trade_record)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
        except Exception as e:
            print(f"Error logging trade: {e}")
