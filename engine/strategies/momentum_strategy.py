class MomentumStrategy:
    def __init__(self, window=10):
        self.window = window
        self.prices = []

    def evaluate(self, market_data):
        price = market_data["price"]
        self.prices.append(price)

        if len(self.prices) < self.window:
            return {"action": "hold"}

        momentum = price - self.prices[-self.window]

        if momentum > 0:
            return {"action": "buy"}
        elif momentum < 0:
            return {"action": "sell"}
        else:
            return {"action": "hold"}
