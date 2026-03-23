from core.live_data_feed import LiveDataFeed
from core.strategy_interface import load_strategy_classes

def evaluate_market():
    feed = LiveDataFeed()
    market_data = feed.get_all()
    strategies = load_strategy_classes()

    results = []

    for data in market_data:
        symbol = data["symbol"]
        price = data["price"]
        timestamp = data["timestamp"]

        for StrategyClass in strategies:
            strat = StrategyClass(symbol)
            decision = strat.evaluate(price=price, timestamp=timestamp)

            if decision == "buy":
                print(f"✅ BUY signal → {symbol} via {strat.__class__.__name__}")
                results.append({
                    "symbol": symbol,
                    "strategy": strat.__class__.__name__,
                    "decision": decision,
                    "price": price,
                    "timestamp": timestamp,
                })

    return results
