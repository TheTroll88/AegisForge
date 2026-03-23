def run_strategy(market_data):
    price = market_data['price']
    resistance = market_data['resistance']
    support = market_data['support']
    if price > resistance:
        return "BUY"
    elif price < support:
        return "SELL"
    return "HOLD"
