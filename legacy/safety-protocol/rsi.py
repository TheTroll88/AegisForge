def run_strategy(market_data):
    rsi = market_data.get("rsi", 50)
    if rsi < 30:
        return "BUY"
    elif rsi > 70:
        return "SELL"
    return "HOLD"
