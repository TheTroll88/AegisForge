# engine/core/whale_signal_bridge.py

"""
Whale Signal Bridge
====================
Bridges whale tracker signals into the trading strategy loop.
Applies sentiment-based weight adjustments to strategy signals
based on recent whale activity.

Design:
- Consumes WhaleTracker.get_recent_signals() periodically
- Maintains a per-token sentiment score: -1.0 (bearish) to +1.0 (bullish)
- Strategy signals pass through adjust_signal() which can:
  - Amplify buy signals when whales are accumulating
  - Amplify sell signals when whales are distributing
  - Suppress signals that contradict strong whale sentiment
  - Pass through unchanged when no whale data exists
"""

import logging
import time
from typing import Optional

logger = logging.getLogger("AegisEngine.WhaleSignalBridge")

# How often to refresh whale sentiment (seconds)
REFRESH_INTERVAL = 60
# How far back to look for signals (minutes)
SIGNAL_LOOKBACK_MINUTES = 30
# Minimum whale signal strength to affect trading decisions
MIN_SIGNAL_STRENGTH = 0.15
# Maximum weight boost from whale signals (caps amplification)
MAX_WEIGHT_BOOST = 0.5


class WhaleSignalBridge:
    """
    Bridges whale tracker signals into strategy weight adjustments.

    Usage:
        bridge = WhaleSignalBridge(whale_tracker)
        # In strategy loop:
        adjusted = bridge.adjust_signal(signal, market_data, strategy_name)
    """

    def __init__(self, whale_tracker):
        self.tracker = whale_tracker
        self._sentiment_cache: dict[str, float] = {}  # token -> sentiment score
        self._last_refresh: float = 0
        self._signal_count: int = 0
        self._adjustments_made: int = 0

    def refresh_sentiment(self):
        """Pull latest whale signals and compute per-token sentiment."""
        now = time.time()
        if now - self._last_refresh < REFRESH_INTERVAL:
            return

        try:
            signals = self.tracker.get_recent_signals(limit=100)
            if not signals:
                self._last_refresh = now
                return

            # Reset sentiment
            sentiment: dict[str, list[float]] = {}

            for sig in signals:
                # Only consider recent signals
                detected_at = sig.get("detected_at", "")
                signal_type = sig.get("signal_type", "")
                total_usd = sig.get("total_usd", 0)
                chain = sig.get("chain", "unknown")

                # Score based on signal type
                if signal_type == "accumulation":
                    score = min(1.0, total_usd / 500_000)  # Scale up to $500k
                elif signal_type == "distribution":
                    score = -min(1.0, total_usd / 500_000)
                elif signal_type == "coordinated":
                    # Coordinated moves are ambiguous — slight bullish bias
                    # (whales moving money = activity = opportunity)
                    score = 0.3 if total_usd > 200_000 else 0.1
                elif signal_type == "large_single":
                    # Large single transfers: neutral to slight positive
                    score = 0.15
                else:
                    score = 0.0

                key = chain.lower()
                if key not in sentiment:
                    sentiment[key] = []
                sentiment[key].append(score)

            # Average scores per chain
            self._sentiment_cache = {}
            for key, scores in sentiment.items():
                if scores:
                    avg = sum(scores) / len(scores)
                    self._sentiment_cache[key] = max(-1.0, min(1.0, avg))

            self._last_refresh = now
            self._signal_count = len(signals)

            if self._sentiment_cache:
                logger.info(
                    f"[WhaleSignalBridge] Refreshed sentiment from {len(signals)} signals: "
                    + ", ".join(f"{k}={v:+.2f}" for k, v in self._sentiment_cache.items())
                )

        except Exception as e:
            logger.warning(f"[WhaleSignalBridge] Failed to refresh sentiment: {e}")

    def get_sentiment(self, chain: str = "base") -> float:
        """Get current whale sentiment for a chain. Returns 0.0 if no data."""
        self.refresh_sentiment()
        return self._sentiment_cache.get(chain.lower(), 0.0)

    def adjust_signal(self, signal: dict, market_data: dict, strategy_name: str = "") -> dict:
        """
        Adjust a strategy signal based on whale sentiment.

        Returns the signal dict, potentially with modified action or added metadata.
        Does NOT override strong strategy convictions — only amplifies or dampens.
        """
        self.refresh_sentiment()

        action = signal.get("action", "hold")
        if action == "hold":
            return signal  # Don't convert holds into trades

        # Determine which chain sentiment to use
        # For now, use "base" as primary since that's where ASIG lives
        symbol = market_data.get("symbol", "")
        sentiment = self._get_best_sentiment(symbol)

        if abs(sentiment) < MIN_SIGNAL_STRENGTH:
            return signal  # Not enough whale data to matter

        # Apply sentiment adjustment
        adjusted = dict(signal)
        adjusted["whale_sentiment"] = round(sentiment, 3)
        adjusted["whale_adjusted"] = True

        if action == "buy" and sentiment > MIN_SIGNAL_STRENGTH:
            # Whale accumulation confirms buy signal — boost confidence
            boost = min(sentiment, MAX_WEIGHT_BOOST)
            adjusted["confidence_boost"] = round(boost, 3)
            adjusted["whale_note"] = "buy confirmed by whale accumulation"
            self._adjustments_made += 1
            logger.debug(f"[WhaleSignalBridge] BUY boosted +{boost:.2f} for {symbol} ({strategy_name})")

        elif action == "sell" and sentiment < -MIN_SIGNAL_STRENGTH:
            # Whale distribution confirms sell signal — boost confidence
            boost = min(abs(sentiment), MAX_WEIGHT_BOOST)
            adjusted["confidence_boost"] = round(boost, 3)
            adjusted["whale_note"] = "sell confirmed by whale distribution"
            self._adjustments_made += 1
            logger.debug(f"[WhaleSignalBridge] SELL boosted +{boost:.2f} for {symbol} ({strategy_name})")

        elif action == "buy" and sentiment < -MIN_SIGNAL_STRENGTH:
            # Whale distribution contradicts buy — suppress to hold
            adjusted["action"] = "hold"
            adjusted["whale_note"] = "buy suppressed — whale distribution detected"
            adjusted["original_action"] = "buy"
            self._adjustments_made += 1
            logger.info(f"[WhaleSignalBridge] BUY suppressed for {symbol} — whale sentiment {sentiment:.2f}")

        elif action == "sell" and sentiment > MIN_SIGNAL_STRENGTH * 2:
            # Strong whale accumulation contradicts sell — suppress to hold
            # Higher threshold for suppression (2x) to avoid blocking valid sells
            adjusted["action"] = "hold"
            adjusted["whale_note"] = "sell suppressed — strong whale accumulation"
            adjusted["original_action"] = "sell"
            self._adjustments_made += 1
            logger.info(f"[WhaleSignalBridge] SELL suppressed for {symbol} — whale sentiment {sentiment:.2f}")

        return adjusted

    def _get_best_sentiment(self, symbol: str) -> float:
        """Try to match symbol to the best available chain sentiment."""
        # If we have chain-specific sentiment, use it
        # Otherwise fall back to overall average
        if not self._sentiment_cache:
            return 0.0

        # Check if symbol hints at a chain
        sym = symbol.upper() if symbol else ""
        if "ETH" in sym or "WETH" in sym:
            if "ethereum" in self._sentiment_cache:
                return self._sentiment_cache["ethereum"]
        if "BNB" in sym or "BSC" in sym:
            if "bsc" in self._sentiment_cache:
                return self._sentiment_cache["bsc"]

        # Default: average all chains
        values = list(self._sentiment_cache.values())
        return sum(values) / len(values) if values else 0.0

    def get_stats(self) -> dict:
        """Return bridge statistics for API/dashboard."""
        return {
            "sentiment_cache": dict(self._sentiment_cache),
            "signals_processed": self._signal_count,
            "adjustments_made": self._adjustments_made,
            "last_refresh": self._last_refresh,
            "active": bool(self._sentiment_cache),
        }
