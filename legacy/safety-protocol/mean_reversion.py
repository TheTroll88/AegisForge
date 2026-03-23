def run_strategy(market_data):
    price = market_data['price']
    mean_price = market_data['mean_price']
    if price < mean_price * 0.95:
        return "BUY"
    elif price > mean_price * 1.05:
        return "SELL"
    return "HOLD"
