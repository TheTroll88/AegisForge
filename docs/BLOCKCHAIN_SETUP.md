# kratos_core/BLOCKCHAIN_SETUP.md

# 🔗 Blockchain & MetaMask Setup Guide

## Quick Start: Micro Trading ($0.01 - $100 per trade)

This guide walks you through connecting your MetaMask wallet and setting up micro-trading on Polygon.

---

## Step 1: Get Your MetaMask Private Key

1. Open MetaMask
2. Click: **Settings** → **Security & Privacy**
3. Click: **Show Private Key**
4. Enter your password and copy your **PRIVATE KEY**
   - ⚠️ **NEVER share this key with anyone!**

---

## Step 2: Configure `.env` File

Edit `.env` in the root folder (`The_Birth_of_a_Pantheon_PhasePort/`):

```env
# MetaMask Wallet
METAMASK_PRIVATE_KEY=123abc456def...  # Your 64-character hex key
METAMASK_WALLET_ADDRESS=0x123...     # Your wallet address (0x...)

# Network (Polygon = cheapest gas)
METAMASK_RPC_URL=https://polygon-rpc.com
METAMASK_CHAIN_ID=137

# Micro Trading Settings
MICRO_TRADING_ENABLED=True
MICRO_TRADING_BASE_AMOUNT=1.0       # Start with $1 per trade
MICRO_TRADING_SCALE_FACTOR=0.01     # 1% of balance max
MICRO_MAX_POSITION_SIZE=100.0       # Never trade more than $100

# Safety Settings
MAX_SLIPPAGE_PERCENT=0.5            # Max 0.5% slippage
MIN_PROFIT_THRESHOLD=0.01           # Trade if profit > $0.01
GAS_PRICE_MULTIPLIER=1.2            # Speedup multiplier
```

---

## Step 3: Fund Your Wallet

You need **Polygon MATIC** for gas fees + **USDC** for trading:

### Via Bridge (Ethereum → Polygon):
1. Go to https://bridge.polygon.technology
2. Connect MetaMask
3. Send USDC/ETH from Ethereum to Polygon
4. Minimum: **$5-10 for initial testing**

### Via Exchange (Direct to Polygon):
- Binance, Kraken, Kucoin support Polygon
- Withdraw USDC or USDT directly to Polygon network

---

## Step 4: Install Dependencies

```bash
cd The_Birth_of_a_Pantheon_PhasePort
pip install -r requirements.txt
```

This installs:
- `web3.py` - Blockchain interactions
- `eth-account` - Wallet/signing

---

## Step 5: Test Your Connection

```bash
python -c "
from kratos_core.core.wallet_manager import WalletManager
wallet = WalletManager()
balance = wallet.get_balance()
print(f'✅ Connected! MATIC Balance: {balance}')
"
```

Expected output:
```
✅ Connected to chain ID: 137
✅ Loaded account: 0x123...
💰 MATIC Balance: 1.234567
```

---

## Step 6: Start Micro Trading

### Option A: Update FastAPI Server

Modify `kratos_core/main_fastapi.py`:

```python
from core.micro_trader import MicroTrader

# Replace PaperTrader with MicroTrader
trader = MicroTrader(logger=logger, trade_logger=trade_logger)
```

Run:
```bash
cd kratos_core
python main_fastapi.py
```

### Option B: Test Directly

```python
from core.wallet_manager import WalletManager
from core.micro_trader import MicroTrader

# Initialize
trader = MicroTrader()

# Execute a trade signal
signal = {"action": "buy"}
market_data = {"symbol": "USDC", "price": 1.0}
trade = trader.execute(signal, market_data, strategy_name="test")

print(trade)
```

---

## Trading Flow

```
Signal Generated
    ↓
Calculate Position Size ($1-$100)
    ↓
Build Uniswap Swap Transaction
    ↓
Sign with MetaMask Private Key
    ↓
Send to Polygon Network
    ↓
Wait for Confirmation (5-30 seconds)
    ↓
Log Trade in trade_log.json
    ↓
Track Profit/Loss in Real-Time
```

---

## Cost Breakdown (Polygon)

| Operation | Gas | Cost |
|-----------|-----|------|
| Token Swap | ~200k | $0.01-0.05 |
| Token Approval | ~50k | $0.002-0.01 |
| **Total per trade** | | **~$0.02-0.10** |

💰 **Result**: With $1 trades, you keep $0.90+ profit on wins, lose ~$1.01 on losses

---

## Safety Checklist

✅ Test with $1 trades first
✅ Verify all TX hashes in BlockScout
✅ Keep private key in `.env` (never commit to git)
✅ Start with `MICRO_TRADING_ENABLED=True`
✅ Monitor gas prices before big trades
✅ Use `MAX_SLIPPAGE_PERCENT=0.5` minimum

---

## Verify Trades

View all your transactions:
- **Polygon BlockScout**: https://polygonscan.com
- **MetaMask Activity Tab**: Shows all TX history

---

## Troubleshooting

### ❌ "Failed to connect to RPC"
- Check internet connection
- Try: `https://polygon.meowrpc.com` as backup

### ❌ "Insufficient balance for gas"
- Need ~0.1 MATIC minimum for ~50 swaps
- Get from: https://faucet.polygon.technology/

### ❌ "Transaction reverted"
- Slippage too high → increase `MAX_SLIPPAGE_PERCENT`
- Liquidity low → try larger swaps or different token pair

---

## Scaling to $30K

Once you've proven consistency with micro amounts:

1. **Keep MICRO_TRADING_ENABLED=True** (size scales with balance)
2. **Increase MICRO_TRADING_BASE_AMOUNT** to $100
3. **Increase MICRO_MAX_POSITION_SIZE** to $5,000
4. **Monitor daily**: If win rate > 60% for 30 days, scale further

---

## Key Differences: Paper vs Micro Trading

| Aspect | Paper | Micro |
|--------|-------|-------|
| **Capital at risk** | $0 | $1-100 |
| **Gas fees** | No | $0.02-0.10 per trade |
| **Slippage** | No | Yes (~0.1-0.5%) |
| **Real profit/loss** | Simulated | Real USDC |
| **Learning value** | 50% → 100% with micro |

---

## Questions?

For technical support:
- Check `kratos_core/logs/trade_log.json` for full trade history
- Monitor blockchain: `https://polygonscan.com/address/YOUR_ADDRESS`
- Test with `UniswapUI`: https://app.uniswap.org on testnet first
