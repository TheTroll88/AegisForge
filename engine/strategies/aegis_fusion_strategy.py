import json
from pathlib import Path

from strategies.rsi_strategy import RSIStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerStrategy
from strategies.breakout_strategy import BreakoutStrategy
from strategies.volume_spike_strategy import VolumeSpikeStrategy

WEIGHTS_PATH = Path(__file__).resolve().parent.parent / "data" / "strategy_weights.json"

# Maps each strategy instance to its weight key
STRATEGY_WEIGHT_KEYS = {
    "RSIStrategy": "rsi",
    "MomentumStrategy": "momentum",
    "MACDStrategy": "macd",
    "BollingerStrategy": "bollinger",
    "BreakoutStrategy": "breakout",
    "VolumeSpikeStrategy": "volume_spike",
}


class AegisFusionStrategy:
    def __init__(self):
        self.strategies = [
            RSIStrategy(),
            MomentumStrategy(),
            MACDStrategy(),
            BollingerStrategy(),
            BreakoutStrategy(),
            VolumeSpikeStrategy(),
        ]
        self.weights = self._load_weights()

    def _load_weights(self) -> dict | None:
        """Load strategy weights from JSON. Returns None if unavailable."""
        try:
            if WEIGHTS_PATH.exists():
                with open(WEIGHTS_PATH, "r") as f:
                    data = json.load(f)
                return data.get("weights", None)
        except (json.JSONDecodeError, OSError):
            pass
        return None

    def reload_weights(self):
        """Reload weights from disk (call after auto-tune runs)."""
        self.weights = self._load_weights()

    def evaluate(self, market_data):
        votes = {"buy": 0.0, "sell": 0.0, "hold": 0.0}

        for strategy in self.strategies:
            signal = strategy.evaluate(market_data)
            action = signal.get("action", "hold")
            class_name = type(strategy).__name__
            weight_key = STRATEGY_WEIGHT_KEYS.get(class_name)

            if self.weights and weight_key and weight_key in self.weights:
                w = self.weights[weight_key]
            else:
                w = 1.0  # equal voting fallback

            votes[action] += w

        if votes["buy"] > votes["sell"] and votes["buy"] > votes["hold"]:
            return {"action": "buy"}
        elif votes["sell"] > votes["buy"] and votes["sell"] > votes["hold"]:
            return {"action": "sell"}
        else:
            return {"action": "hold"}
