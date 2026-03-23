class RSITrendStrategy:
    def __init__(self, rsi_period=14, overbought=65, oversold=35, short_window=5, long_window=20):
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        self.short_window = short_window
        self.long_window = long_window
        self.prices = []

    def _calculate_rsi(self, prices):
        if len(prices) < 2:
            return 50

        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))

        avg_gain = sum(gains) / self.rsi_period if gains else 0
        avg_loss = sum(losses) / self.rsi_period if losses else 0
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _sma(self, window):
        if len(self.prices) < window:
            return None
        return sum(self.prices[-window:]) / window

    def evaluate(self, market_data):
        price = market_data.get("price")
        if price is None:
            return {"action": "hold"}
        self.prices.append(price)

        if len(self.prices) < max(self.rsi_period + 1, self.long_window):
            return {"action": "hold"}

        rsi = self._calculate_rsi(self.prices[-self.rsi_period:])
        short_sma = self._sma(self.short_window)
        long_sma = self._sma(self.long_window)
        if short_sma is None or long_sma is None:
            return {"action": "hold"}

        uptrend = short_sma > long_sma
        downtrend = short_sma < long_sma

        if rsi < self.oversold and uptrend:
            return {"action": "buy"}
        if rsi > self.overbought and downtrend:
            return {"action": "sell"}
        return {"action": "hold"}
