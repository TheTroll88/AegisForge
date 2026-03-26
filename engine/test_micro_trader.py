#!/usr/bin/env python3
# engine/test_micro_trader.py

"""
Test script for Micro Trader (live blockchain trading with small amounts)
Run: python test_micro_trader.py
"""

import sys
import os
from pathlib import Path

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from pathlib import Path

# Ensure .env from project root is loaded
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

from core.micro_trader import MicroTrader
from core.logger import setup_logger


import time
from core.live_data_feed import LiveDataFeed
from core.strategies.rsi_strategy import RSIStrategy
from core.strategies.rsi_trend_strategy import RSITrendStrategy

def main():
    logger = setup_logger()
    logger.info("🚀 Starting real-time MicroTrader simulation...")
    try:
        trader = MicroTrader(logger=logger)
        logger.info(f"✅ MicroTrader initialized")
        feed = LiveDataFeed()
        allowed = trader.allowed_tokens
        strategy_key = os.getenv("STRATEGY_NAME", "rsi").lower()
        if strategy_key in ("rsi_trend", "rsi-trend"):
            strategy_name = "rsi_trend"
            strategy_cls = RSITrendStrategy
        else:
            strategy_name = "rsi"
            strategy_cls = RSIStrategy
        strategies = {t: strategy_cls() for t in allowed}
        logger.info(f"Simulating on tokens: {allowed}")
        logger.info("Press Ctrl+C to stop simulation at any time.")
        while True:
            for symbol in allowed:
                is_address = isinstance(symbol, str) and symbol.startswith("0x") and len(symbol) == 42
                symbol_key = symbol if is_address else str(symbol).upper()
                quote_symbol = os.getenv("DEFAULT_QUOTE_TOKEN", "ETH").upper()
                if trader.dex:
                    price = trader.dex.get_price_in_quote(symbol_key, quote_symbol)
                else:
                    price = None

                if not price:
                    logger.warning(f"⚠️ Could not fetch on-chain price for {symbol_key}/{quote_symbol}")
                    continue
                if not price:
                    continue
                # Simple strategy: buy if no position, sell if TP/SL hit
                strategy = strategies.get(symbol_key)
                signal = strategy.evaluate({"symbol": symbol_key, "price": price}) if strategy else {"action": "hold"}
                if symbol_key not in trader.positions:
                    if signal.get("action") != "buy":
                        continue
                    buy_signal = {"action": "buy"}
                    market_data = {"symbol": symbol_key, "price": price, "timestamp": time.time()}
                    trade = trader.execute(buy_signal, market_data, strategy_name=strategy_name)
                    if trade:
                        logger.info(f"✅ Buy executed: {trade}")
                else:
                    entry = trader.positions[symbol_key]
                    entry_price = entry["entry_price"]
                    tp = entry_price * (1 + trader.tp_percent / 100)
                    sl = entry_price * (1 - trader.sl_percent / 100)
                    if signal.get("action") == "sell" or price >= tp or price <= sl:
                        sell_signal = {"action": "sell"}
                        market_data = {"symbol": symbol_key, "price": price, "timestamp": time.time()}
                        trade = trader.execute(sell_signal, market_data, strategy_name=strategy_name)
                        if trade:
                            logger.info(f"✅ Sell executed: {trade}")
            # Print stats every loop
            stats = trader.get_stats()
            logger.info(f"[STATS] Trades: {stats['total_trades']} | Win Rate: {stats['win_rate']:.1f}% | P&L: ${stats['total_pnl']:.4f}")
            time.sleep(10)  # Wait 10 seconds between cycles
    except KeyboardInterrupt:
        logger.info("🛑 Simulation stopped by user.")
        stats = trader.get_stats()
        logger.info(f"Final Stats: {stats}")
    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
