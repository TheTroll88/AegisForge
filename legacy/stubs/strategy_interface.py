from strategies.momentum_strategy import MomentumStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.breakout_strategy import BreakoutStrategy
from strategies.volume_spike_strategy import VolumeSpikeStrategy
from strategies.aegis_fusion_strategy import AegisFusionStrategy

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
