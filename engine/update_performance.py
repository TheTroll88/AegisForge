import json
import os

# Define paths
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
trade_log_path = os.path.join(log_dir, 'trade_log.json')
performance_path = os.path.join(log_dir, 'performance.json')

# Load trade logs
with open(trade_log_path, 'r') as file:
    trades = json.load(file)

# Calculate performance metrics
total_trades = len(trades)
wins = sum(1 for t in trades if t['outcome'] == 'win')
losses = total_trades - wins
profit_loss = sum(t['profit'] for t in trades)
roi_sum = sum(t['roi'] for t in trades if 'roi' in t and isinstance(t['roi'], (int, float)))

# Avoid divide-by-zero
win_rate = (wins / total_trades) * 100 if total_trades else 0
average_roi = (roi_sum / total_trades) if total_trades else 0

# Save updated performance metrics
performance_data = {
    "total_trades": total_trades,
    "win_rate": round(win_rate, 2),
    "profit_loss": round(profit_loss, 2),
    "average_roi": round(average_roi, 2)
}

with open(performance_path, 'w') as file:
    json.dump(performance_data, file, indent=2)

print("✅ performance.json updated with live data.")
