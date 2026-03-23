import logging
import os
from typing import Optional

from core.wallet_manager import WalletManager
from core.dex_trader import DEXTrader


class LiveDataFeed:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_quote = os.getenv("DEFAULT_QUOTE_TOKEN", "USDC")
        self.wallet = WalletManager(logger=self.logger)
        self.dex = DEXTrader(self.wallet, logger=self.logger)

    def get_price(self, symbol: str) -> Optional[float]:
        """Fetch current price using on-chain quoter. Accepts 'TOKEN/QUOTE' or 'TOKEN'."""
        try:
            pair = symbol.strip()
            if "/" in pair:
                base, quote = pair.split("/", 1)
            else:
                base, quote = pair, self.default_quote
            base = base.strip()
            quote = quote.strip()

            base_key = base.upper()
            quote_key = quote.upper()

            # Treat native ETH as WETH for on-chain pricing
            if base_key in ("ETH", "NATIVE"):
                base = "WETH"
                base_key = "WETH"
            if quote_key in ("ETH", "NATIVE"):
                quote = "WETH"
                quote_key = "WETH"

            if base_key == quote_key:
                return 1.0

            price = self.dex.get_price_in_quote(base, quote)
            if not price:
                self.logger.warning(f"⚠️ Could not fetch on-chain price for {base}/{quote}")
            return price
        except Exception as e:
            self.logger.warning(f"⚠️ Could not fetch price for {symbol}: {e}")
            return None
