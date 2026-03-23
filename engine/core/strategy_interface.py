from core.strategies.momentum_strategy import MomentumStrategy
from core.strategies.rsi_strategy import RSIStrategy
from core.strategies.macd_strategy import MACDStrategy
from core.strategies.bollinger_strategy import BollingerStrategy
from core.strategies.breakout_strategy import BreakoutStrategy
from core.strategies.volume_spike_strategy import VolumeSpikeStrategy
from core.strategies.aegis_fusion_strategy import AegisFusionStrategy

def load_strategies():
    return [
        MomentumStrategy(),
        RSIStrategy(),
        MACDStrategy(),
        BollingerStrategy(),
        BreakoutStrategy(),
        VolumeSpikeStrategy(),
        AegisFusionStrategy()  # Super bot
    ]
