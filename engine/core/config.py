# engine/core/config.py

class TraderConfig:
    # ==== MODE SELECTION ====
    PAPER_MODE = False              # Paper trading (simulated, no real money)
    LIVE_MODE = False               # Live Binance trading (for real money)
    MICRO_MODE = True               # Micro blockchain trading ($0.01-$100, starts small)
    
    # ==== BINANCE LIVE TRADING ====
    LIVE_EXCHANGE = False           # Enable live Binance trading
    KILL_SWITCH = False             # Manual safety override
    EXCHANGE_ID = "binanceus"       # Set your exchange here
    USE_SANDBOX = False             # Optional: sandbox testing
    
    # ==== MICRO TRADING (POLYGON BLOCKCHAIN) ====
    MICRO_ENABLED = True
    MICRO_BASE_AMOUNT = 1.0         # Start with $1 per trade
    MICRO_MAX_POSITION = 100.0      # Max $100 per trade
    MICRO_SCALE_WITH_BALANCE = True # Scale position size with wallet balance
    
    # ==== RISK MANAGEMENT ====
    POSITION_SIZE_PERCENT = 1.0     # 1% of portfolio per trade
    MAX_DAILY_LOSS_PERCENT = 5.0    # Stop trading if daily loss > 5%
    MAX_DRAWDOWN_PERCENT = 15.0     # Stop all trading if drawdown > 15%
    
    # ==== SLIPPAGE & FEES ====
    MAX_SLIPPAGE_PERCENT = 0.5      # Max acceptable slippage
    GAS_PRICE_MULTIPLIER = 1.2      # Gas price adjustment
    MIN_PROFIT_THRESHOLD = 0.01     # Minimum profit to trade ($0.01)
    # ==== TAKE-PROFIT / STOP-LOSS (percent) ====
    TAKE_PROFIT_PERCENT = 2.0       # Take profit at +2%
    STOP_LOSS_PERCENT = 1.0         # Stop loss at -1%
