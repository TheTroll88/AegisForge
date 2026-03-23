def run_strategy(market_data):
    macd = market_data.get("macd", 0)
    signal = market_data.get("signal", 0)
    if macd > signal:
        return "BUY"
    elif macd < signal:
        return "SELL"
    return "HOLD"
