def run_strategy(market_data):
    short_ma = sum(market_data['prices'][-5:]) / 5
    long_ma = sum(market_data['prices'][-20:]) / 20
    if short_ma > long_ma:
        return "BUY"
    return "SELL"
