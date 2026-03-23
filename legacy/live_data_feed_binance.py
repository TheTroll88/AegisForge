import ccxt
import logging
from datetime import datetime

class LiveDataFeed:
    def __init__(self, exchange_id="binanceus"):
        self.logger = logging.getLogger(__name__)
        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                "enableRateLimit": True,
            })
            self.exchange.load_markets()

            # Automatically scan all active USDT pairs
            self.symbols = [s for s in self.exchange.markets
                            if s.endswith("/USDT") and self.exchange.markets[s].get("active")]
            if not self.symbols:
                raise ValueError("No valid USDT markets found on this exchange.")

            self.logger.info(f"✅ Loaded {len(self.symbols)} active USDT markets from {exchange_id}")
        except Exception as e:
            self.logger.error(f"❌ Error initializing exchange {exchange_id}: {e}")
            raise

    def get_all(self):
        """Fetches latest prices for all symbols."""
        live_data = []
        for symbol in self.symbols:
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                price = ticker.get("last")
                timestamp = ticker.get("timestamp")

                if not price or not timestamp:
                    continue  # Skip incomplete data

                readable_time = datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.logger.info(f"📈 {symbol} → ${price:.4f} @ {readable_time} UTC")

                live_data.append({
                    "symbol": symbol,
                    "price": price,
                    "timestamp": timestamp
                })

            except Exception as e:
                self.logger.warning(f"⚠️ Failed to fetch {symbol}: {e}")
                continue

        return live_data

    def get_price(self, symbol: str):
        """Fetches current price for a specific symbol like 'BTC/USDT'."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker.get("last")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not fetch price for {symbol}: {e}")
            return None
