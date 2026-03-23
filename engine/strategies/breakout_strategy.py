class BreakoutStrategy:
    def __init__(self, lookback=15):
        self.lookback = lookback
        self.prices = []

    def evaluate(self, market_data):
        price = market_data["price"]
        self.prices.append(price)

        if len(self.prices) < self.lookback:
            return {"action": "hold"}

        recent_prices = self.prices[-self.lookback:]
        highest = max(recent_prices)
        lowest = min(recent_prices)

        if price >= highest:
            return {"action": "buy"}
        elif price <= lowest:
            return {"action": "sell"}
        else:
            return {"action": "hold"}
