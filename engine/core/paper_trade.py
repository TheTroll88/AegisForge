# engine/core/paper_trade.py

import logging
from datetime import datetime
from .config import TraderConfig

class PaperTrader:
    def __init__(self, logger=None, trade_logger=None, starting_balance=10000):
        self.logger = logger or logging.getLogger(__name__)
        self.trade_logger = trade_logger
        self.balance = starting_balance
        self.position = None
        self.entry_price = None
        self.wins = 0
        self.losses = 0
        self.trade_count = 0
        self.live_mode = TraderConfig.LIVE_MODE
        self.kill_switch = TraderConfig.KILL_SWITCH

    def execute(self, signal: dict, market_data: dict, strategy_name: str = "unknown"):
        action = signal.get("action", "hold")
        symbol = market_data.get("symbol", "UNKNOWN")
        price = market_data.get("price", 0)
        timestamp = market_data.get("timestamp") or datetime.utcnow().isoformat()

        if self.kill_switch and self.live_mode:
            self.logger.warning("🛑 KILL SWITCH ACTIVATED: Trade skipped")
            return

        trade_data = {
            "strategy": strategy_name,
            "action": action,
            "symbol": symbol,
            "price": price,
            "timestamp": timestamp,
            "mode": "LIVE" if self.live_mode else "PAPER"
        }

        if action == "buy":
            self.logger.info(f"🟩 BUY {symbol} @ ${price} [{trade_data['mode']}]")
            self.position = "long"
            self.entry_price = price

        elif action == "sell":
            self.logger.info(f"🟥 SELL {symbol} @ ${price} [{trade_data['mode']}]")
            if self.position == "long" and self.entry_price is not None:
                profit = round(price - self.entry_price, 2)
                roi = round((profit / self.entry_price) * 100, 2)
                result = "win" if profit > 0 else "loss"

                trade_data.update({
                    "result": result,
                    "roi": roi,
                    "profit": profit
                })

                if result == "win":
                    self.wins += 1
                    self.logger.info(f"🏆 WIN: +${profit} | ROI: {roi}%")
                else:
                    self.losses += 1
                    self.logger.info(f"💀 LOSS: ${profit} | ROI: {roi}%")

                self.balance += profit

            self.position = None
            self.entry_price = None

        elif action == "hold":
            self.logger.info(f"⏸️ HOLD {symbol} - no action [{trade_data['mode']}]")
        else:
            self.logger.warning(f"❓ Unknown action: {action}")

        if action in ["buy", "sell"]:
            self.trade_count += 1
            if self.trade_logger:
                self.trade_logger.log(trade_data)

        self.logger.info(
            f"📊 [{trade_data['mode']}] Balance: ${round(self.balance, 2)} | Trades: {self.trade_count} | 🟢 Wins: {self.wins} | 🔴 Losses: {self.losses}"
        )
