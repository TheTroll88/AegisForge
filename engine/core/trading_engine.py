import logging
import time
from core.live_data_feed import LiveDataFeed

class TradingEngine:
    def __init__(self, strategies, trader, logger=None, delay=2):
        self.strategies = strategies
        self.data_feed = LiveDataFeed()
        self.trader = trader
        self.logger = logger or logging.getLogger(__name__)
        self.delay = delay  # ⏱️ seconds between ticks

    def run(self, max_iterations=10):
        self.logger.info("🚀 Trading engine run started.")
        iterations = 0

        while iterations < max_iterations:
            market_batch = self.data_feed.get_all()

            if not market_batch:
                self.logger.warning("⚠️ Market data fetch failed. Skipping this iteration.")
                time.sleep(self.delay)
                continue

            for market_data in market_batch:
                for strategy in self.strategies:
                    try:
                        signal = strategy.evaluate(market_data)
                        if signal and signal.get("action") != "hold":
                            self.logger.info(f"📡 Signal from {strategy.__class__.__name__} on {market_data['symbol']}: {signal}")
                            self.trader.execute(signal, market_data, strategy_name=strategy.__class__.__name__)
                        else:
                            self.logger.debug(f"🧠 HOLD from {strategy.__class__.__name__} on {market_data['symbol']}")
                    except Exception as e:
                        self.logger.error(f"🔥 Strategy error [{strategy.__class__.__name__}]: {e}")

            iterations += 1
            time.sleep(self.delay)
