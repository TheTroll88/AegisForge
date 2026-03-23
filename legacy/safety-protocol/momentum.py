def run_strategy(market_data):
    print("Running momentum strategy...")
    return "BUY" if market_data.get("trend") == "up" else "SELL"
