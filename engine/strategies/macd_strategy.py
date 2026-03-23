class MACDStrategy:
    def __init__(self, short_window=12, long_window=26, signal_window=9):
        self.prices = []
        self.short_window = short_window
        self.long_window = long_window
        self.signal_window = signal_window
        self.macd_line_history = []

    def calculate_ema(self, prices, window):
        k = 2 / (window + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = price * k + ema * (1 - k)
        return ema

    def evaluate(self, market_data):
        price = market_data["price"]
        self.prices.append(price)

        if len(self.prices) < self.long_window:
            return {"action": "hold"}

        short_ema = self.calculate_ema(self.prices[-self.short_window:], self.short_window)
        long_ema = self.calculate_ema(self.prices[-self.long_window:], self.long_window)
        macd_line = short_ema - long_ema

        self.macd_line_history.append(macd_line)

        if len(self.macd_line_history) < self.signal_window:
            return {"action": "hold"}

        signal_line = self.calculate_ema(self.macd_line_history[-self.signal_window:], self.signal_window)

        if macd_line > signal_line:
            return {"action": "buy"}
        elif macd_line < signal_line:
            return {"action": "sell"}
        else:
            return {"action": "hold"}
