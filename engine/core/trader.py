# engine/core/trader.py

import time
from datetime import datetime
from core.strategy_interface import load_strategies

class PaperTrader:
    def __init__(self, logger, trade_logger=None):
        self.logger = logger
        self.trade_logger = trade_logger
        self.strategies = load_strategies()

    def execute(self, signal, market_data, strategy_name=None):
        """Execute a trade signal"""
        try:
            symbol = market_data.get('symbol', 'UNKNOWN')
            price = market_data.get('price', 0)
            action = signal.get('action', 'hold')
            
            if action != 'hold':
                self.logger.info(f"[PAPER TRADE] {action.upper()} → {symbol} @ ${price:.4f} by {strategy_name or 'unknown'}")
                # Create a simple trade record for logging
                if self.trade_logger:
                    import random
                    trade_record = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "symbol": symbol,
                        "action": action,
                        "price": price,
                        "strategy": strategy_name or 'unknown',
                        "success": random.random() > 0.5,  # Simulate 50/50 win/loss for now
                        "roi": round(random.uniform(-0.05, 0.15), 4)
                    }
                    self.trade_logger.log_simple(trade_record)
        except Exception as e:
            self.logger.warning(f"[⚠️ Trader Error] {e}")
