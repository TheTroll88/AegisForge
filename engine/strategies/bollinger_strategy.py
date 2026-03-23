class BollingerStrategy:
    def __init__(self, window=20, num_std_dev=2):
        self.window = window
        self.num_std_dev = num_std_dev
        self.prices = []

    def evaluate(self, market_data):
        price = market_data["price"]
        self.prices.append(price)

        if len(self.prices) < self.window:
            return {"action": "hold"}

        recent_prices = self.prices[-self.window:]
        avg = sum(recent_prices) / self.window
        std_dev = (sum([(p - avg) ** 2 for p in recent_prices]) / self.window) ** 0.5
        upper_band = avg + self.num_std_dev * std_dev
        lower_band = avg - self.num_std_dev * std_dev

        if price > upper_band:
            return {"action": "sell"}
        elif price < lower_band:
            return {"action": "buy"}
        else:
            return {"action": "hold"}
