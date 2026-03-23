import logging

from core.trading_engine import TradingEngine
from core.paper_trade import PaperTrader
from core.live_data_feed import LiveDataFeed
from core.trade_logger import TradeLogger

from core.strategies.rsi_strategy import RSIStrategy
from core.strategies.momentum_strategy import MomentumStrategy
from core.strategies.macd_strategy import MACDStrategy
from core.strategies.bollinger_strategy import BollingerStrategy
from core.strategies.breakout_strategy import BreakoutStrategy
from core.strategies.volume_spike_strategy import VolumeSpikeStrategy
from core.strategies.aegis_fusion_strategy import AegisFusionStrategy


def main():
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
    logger = logging.getLogger()

    logger.info("🚀 Starting AegisForge trading engine...")

    strategies = [
        MomentumStrategy(),
        RSIStrategy(),
        MACDStrategy(),
        BollingerStrategy(),
        BreakoutStrategy(),
        VolumeSpikeStrategy(),
        AegisFusionStrategy()
    ]
    logger.info(f"✅ Loaded {len(strategies)} strategies.")

    data_feed = LiveDataFeed()
    logger.info("🔌 Live market data feed initialized.")

    trade_logger = TradeLogger()
    trader = PaperTrader(logger=logger, trade_logger=trade_logger)
    logger.info("🧾 Paper trader initialized with trade logging.")

    engine = TradingEngine(strategies, data_feed, trader, logger=logger)
    engine.run(max_iterations=100)


if __name__ == "__main__":
    main()
