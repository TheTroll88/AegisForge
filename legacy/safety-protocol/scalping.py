def run_strategy(market_data):
    spread = market_data['ask'] - market_data['bid']
    if spread < 0.5:
        return "BUY"
    return "HOLD"
