from core.strategies.rsi_strategy import RSIStrategy
from core.strategies.momentum_strategy import MomentumStrategy
from core.strategies.macd_strategy import MACDStrategy
from core.strategies.bollinger_strategy import BollingerStrategy
from core.strategies.breakout_strategy import BreakoutStrategy
from core.strategies.volume_spike_strategy import VolumeSpikeStrategy

class AegisFusionStrategy:
    def __init__(self):
        self.strategies = [
            RSIStrategy(),
            MomentumStrategy(),
            MACDStrategy(),
            BollingerStrategy(),
            BreakoutStrategy(),
            VolumeSpikeStrategy()
        ]

    def evaluate(self, market_data):
        votes = {"buy": 0, "sell": 0, "hold": 0}

        for strategy in self.strategies:
            signal = strategy.evaluate(market_data)
            action = signal.get("action", "hold")
            votes[action] += 1

        if votes["buy"] > votes["sell"] and votes["buy"] > votes["hold"]:
            return {"action": "buy"}
        elif votes["sell"] > votes["buy"] and votes["sell"] > votes["hold"]:
            return {"action": "sell"}
        else:
            return {"action": "hold"}
