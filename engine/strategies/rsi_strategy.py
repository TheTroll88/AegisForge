class RSIStrategy:
    def __init__(self, period=14, overbought=70, oversold=30, max_history=200):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.max_history = max_history
        self.prices = []

    def _calculate_rsi(self, prices):
        if len(prices) < self.period + 1:
            return None

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]

        avg_gain = sum(gains[-self.period:]) / self.period if gains else 0
        avg_loss = sum(losses[-self.period:]) / self.period if losses else 0

        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def evaluate(self, market_data):
        price = market_data.get("price")
        if price is None:
            return {"action": "hold"}

        self.prices.append(price)
        if len(self.prices) > self.max_history:
            self.prices = self.prices[-self.max_history:]

        rsi = self._calculate_rsi(self.prices)
        if rsi is None:
            return {"action": "hold"}

        if rsi > self.overbought:
            return {"action": "sell", "rsi": rsi}
        if rsi < self.oversold:
            return {"action": "buy", "rsi": rsi}
        return {"action": "hold", "rsi": rsi}
