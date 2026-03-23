def run_strategy(market_data):
    volume = market_data['volume']
    avg_volume = market_data['avg_volume']
    if volume > avg_volume * 2:
        return "BUY"
    return "HOLD"
