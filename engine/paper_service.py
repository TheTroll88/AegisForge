"""
AegisForge Paper Trading Service
Runs the trading engine in paper mode as a persistent background process.
Managed via manage_paper.ps1 (start/stop/status).

Usage:
    cd engine
    python paper_service.py              # run forever (default)
    python paper_service.py --hours 24   # run for 24 hours
"""

import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from core.trading_engine import TradingEngine
from core.paper_trade import PaperTrader
from core.live_data_feed import LiveDataFeed
from core.trade_logger import TradeLogger

from strategies.rsi_strategy import RSIStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.breakout_strategy import BreakoutStrategy
from strategies.volume_spike_strategy import VolumeSpikeStrategy
from strategies.aegis_fusion_strategy import AegisFusionStrategy
from strategies.rsi_trend_strategy import RSITrendStrategy


# --- Globals ---
running = True
LOG_DIR = Path(__file__).resolve().parent / "logs"
PID_FILE = LOG_DIR / "paper_service.pid"


def shutdown(signum, frame):
    global running
    logging.getLogger().info(f"🛑 Shutdown signal received ({signum}). Stopping gracefully...")
    running = False


def write_pid():
    os.makedirs(LOG_DIR, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def clear_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AegisForge Paper Trading Service")
    parser.add_argument("--hours", type=float, default=0, help="Run for N hours (0 = forever)")
    parser.add_argument("--delay", type=int, default=3, help="Seconds between market scans (default: 3)")
    args = parser.parse_args()

    # Logging
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = LOG_DIR / f"paper_service_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger()

    # Signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # PID file
    write_pid()
    logger.info(f"📝 PID {os.getpid()} written to {PID_FILE.name}")

    # Strategies
    strategies = [
        MomentumStrategy(),
        RSIStrategy(),
        MACDStrategy(),
        BollingerStrategy(),
        BreakoutStrategy(),
        VolumeSpikeStrategy(),
        AegisFusionStrategy(),
        RSITrendStrategy(),
    ]
    logger.info(f"✅ Loaded {len(strategies)} strategies")

    # Engine components
    data_feed = LiveDataFeed()
    trade_logger = TradeLogger()
    trader = PaperTrader(logger=logger, trade_logger=trade_logger)
    logger.info(f"🧾 Paper trader initialized | Balance: ${trader.balance:,.2f}")

    # Run loop
    deadline = None
    if args.hours > 0:
        deadline = datetime.now() + timedelta(hours=args.hours)
        logger.info(f"⏱️  Running for {args.hours} hours (until {deadline.strftime('%H:%M:%S')})")
    else:
        logger.info("♾️  Running indefinitely (Ctrl+C to stop)")

    iteration = 0
    while running:
        if deadline and datetime.now() >= deadline:
            logger.info("⏱️  Time limit reached. Shutting down.")
            break

        try:
            market_batch = data_feed.get_all()
            if not market_batch:
                logger.warning("⚠️ No market data. Retrying in 10s...")
                time.sleep(10)
                continue

            for market_data in market_batch:
                for strategy in strategies:
                    if not running:
                        break
                    try:
                        signal_result = strategy.evaluate(market_data)
                        if signal_result and signal_result.get("action") != "hold":
                            trader.execute(signal_result, market_data, strategy_name=strategy.__class__.__name__)
                    except Exception as e:
                        logger.error(f"Strategy {strategy.__class__.__name__} error: {e}")

            # Check TP/SL on open positions
            if hasattr(trader, "check_positions"):
                trader.check_positions()

            iteration += 1
            if iteration % 100 == 0:
                logger.info(f"📊 Iteration {iteration} | Balance: ${trader.balance:,.2f} | Trades: {trader.wins + trader.losses}")

        except Exception as e:
            logger.error(f"🔥 Loop error: {e}")
            time.sleep(5)

        time.sleep(args.delay)

    # Cleanup
    clear_pid()
    total_trades = trader.wins + trader.losses
    logger.info(f"🏁 Service stopped. Final balance: ${trader.balance:,.2f} | Trades: {total_trades} | Win rate: {(trader.wins / total_trades * 100) if total_trades else 0:.1f}%")


if __name__ == "__main__":
    main()
