class MarketDataFetcher:
    def __init__(self):
        self.counter = 0

    def get_next(self):
        # Simulate market data updates
        self.counter += 1
        return {
            "BTC": {"price": 30000 + self.counter},
            "ETH": {"price": 2000 + self.counter}
        }
