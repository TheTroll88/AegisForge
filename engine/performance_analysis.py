import json
from collections import defaultdict

with open('logs/trade_log.json', 'r') as f:
    trades = json.load(f)

total = len(trades)
wins = sum(1 for t in trades if t.get('success'))
roi_sum = sum(t.get('roi', 0) for t in trades)

# Per strategy breakdown
strat_data = defaultdict(lambda: {'wins': 0, 'losses': 0, 'roi': 0, 'trades': 0})
for t in trades:
    s = t.get('strategy', 'unknown')
    strat_data[s]['trades'] += 1
    if t.get('success'):
        strat_data[s]['wins'] += 1
    else:
        strat_data[s]['losses'] += 1
    strat_data[s]['roi'] += t.get('roi', 0)

print("=== OVERALL PERFORMANCE ===")
print(f"Total Trades: {total}")
print(f"Win Rate: {((wins/total)*100):.2f}%")
print(f"Avg ROI: {(roi_sum/total):.4f}")
print(f"Cumulative ROI: {roi_sum:.4f}")
print(f"\n=== PER STRATEGY ===")

sorted_strats = sorted(strat_data.items(), key=lambda x: (x[1]['wins'] / x[1]['trades']) if x[1]['trades'] > 0 else 0, reverse=True)

for strat, d in sorted_strats:
    win_rate = ((d['wins'] / d['trades']) * 100) if d['trades'] > 0 else 0
    avg_roi = (d['roi'] / d['trades']) if d['trades'] > 0 else 0
    status = "✅" if win_rate > 50 else "⚠️"
    print(f"{status} {strat.upper():18} | Trades: {d['trades']:4d} | Wins: {d['wins']:4d} | Rate: {win_rate:5.2f}% | Avg ROI: {avg_roi:7.4f} | Total ROI: {d['roi']:8.4f}")
