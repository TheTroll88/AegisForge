def run_strategy(market_data):
    price = market_data['price']
    upper_band = market_data['upper_band']
    lower_band = market_data['lower_band']
    if price < lower_band:
        return "BUY"
    elif price > upper_band:
        return "SELL"
    return "HOLD"
