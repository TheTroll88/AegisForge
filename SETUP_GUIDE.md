# 🚀 AegisForge Setup Guide

## Prerequisites

- Python 3.9+
- `git`
- A funded wallet on Base (for micro/live trading) or no wallet needed (paper trading)

---

## Step 1: Clone and Install

```bash
git clone https://github.com/TheTroll88/AegisForge.git
cd AegisForge
pip install -r requirements.txt
```

---

## Step 2: Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Key variables:

| Variable | Description | Required For |
|----------|-------------|--------------|
| `METAMASK_PRIVATE_KEY` | Your wallet private key | Micro / Live trading |
| `METAMASK_WALLET_ADDRESS` | Your wallet address (0x…) | Micro / Live trading |
| `METAMASK_RPC_URL` | Base RPC endpoint | All on-chain modes |
| `METAMASK_CHAIN_ID` | Chain ID (8453 = Base mainnet, 84532 = Base Sepolia) | All on-chain modes |
| `OPENAI_API_KEY` | OpenRouter or OpenAI key | AI chat endpoint |
| `ETHERSCAN_API_KEY` | Etherscan API key | Whale tracker (Ethereum) |
| `BASESCAN_API_KEY` | BaseScan API key | Whale tracker (Base) |
| `PAPER_MODE` | `true` to enable paper trading | Paper trading |
| `MICRO_MODE` | `true` to enable micro trading | Micro trading |

> ⚠️ **Never commit your `.env` file.** It is gitignored by default.

---

## Step 3: Choose a Trading Mode

### Paper Trading (Recommended: Start Here)

No wallet or funds needed. Simulates trades with a virtual $10,000 balance.

```bash
# In .env:
PAPER_MODE=true
MICRO_MODE=false
```

Start the engine:

```bash
cd engine
python run_engine.py
```

Or start the FastAPI server:

```bash
cd engine
python main_fastapi.py
```

---

### Micro Trading (Real on-chain trades, $0.01–$100)

Requires a funded Base wallet with ETH for gas and a small USDC balance.

```bash
# In .env:
PAPER_MODE=false
MICRO_MODE=true
METAMASK_PRIVATE_KEY=0xYOUR_KEY
METAMASK_WALLET_ADDRESS=0xYOUR_ADDRESS
METAMASK_RPC_URL=https://mainnet.base.org
METAMASK_CHAIN_ID=8453
```

Run:

```bash
cd engine
python test_micro_trader.py
```

---

### Live Trading (Binance, full capital)

Only after proven micro trading success. Requires Binance API keys.

```bash
# In .env:
PAPER_MODE=false
MICRO_MODE=false
LIVE_MODE=true
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

---

## Step 4: Wallet Setup (Micro / Live Trading)

### Get ETH on Base

**Option A: Bridge from Ethereum**
1. Go to https://bridge.base.org
2. Connect your wallet
3. Bridge ETH to Base mainnet

**Option B: Buy on Coinbase**
- Withdraw ETH directly to Base network

**Option C: Base Sepolia testnet (testing only)**
- Get test ETH from https://www.coinbase.com/faucets/base-ethereum-goerli-faucet
- Use `METAMASK_RPC_URL=https://sepolia.base.org` and `METAMASK_CHAIN_ID=84532`

---

## Step 5: Verify Setup

### Test Data Feed

```bash
cd engine
python test_data_feed.py
```

Expected output:
```
✅ LiveDataFeed initialized
💰 Price: 0.000123 ETH
```

### Test Wallet Connection

```bash
cd engine
python -c "
from core.wallet_manager import WalletManager
w = WalletManager()
print('Balance:', w.get_balance())
"
```

---

## Whale Tracker

The whale tracker monitors large token transfers across Ethereum, Base, and BSC.

Configure API keys in `.env`:
```env
ETHERSCAN_API_KEY=your-key
BASESCAN_API_KEY=your-key
BSCSCAN_API_KEY=your-key
```

Start standalone:
```bash
cd engine/core
python whale_tracker.py
```

Or use the `/whale-alerts` endpoint when the FastAPI server is running.

---

## Smart Contracts (Base Mainnet)

AegisForge has two deployed contracts on Base:

| Contract | Address |
|----------|---------|
| ASIG Token | `0x30610a21764bb38c43a2e532cfba91c9db927994` |
| SignalRegistry | `0xb5AFac365FD2968157EFF7183144e46F11772926` |

These are integrated via `engine/core/asig_bridge.py`.

---

## Airdrop Farmer (Standalone)

The airdrop farmer runs independently from the trading engine.

```bash
cd airdrop-farmer
cp .env.example .env
# Edit .env with your settings (DRY_RUN=true by default)
python farmer.py
```

---

## FastAPI Server Endpoints

When running `python main_fastapi.py` from the `engine/` directory:

| Endpoint | Description |
|----------|-------------|
| `GET /` | Server status |
| `GET /strategies` | List active strategies |
| `POST /strategy/toggle` | Enable/disable a strategy |
| `GET /performance` | Trading performance summary |
| `GET /whale-alerts` | Recent whale movements |
| `POST /chat` | AI chat (requires OPENAI_API_KEY) |

---

## Troubleshooting

### "Failed to connect to RPC"
- Check your `METAMASK_RPC_URL` in `.env`
- Try a public fallback: `https://mainnet.base.org`

### "Chain ID mismatch"
- Ensure `METAMASK_CHAIN_ID` matches your RPC endpoint
- Base mainnet = 8453, Base Sepolia = 84532

### "No private key found"
- For paper trading this is fine — read-only mode works
- For micro/live trading, set `METAMASK_PRIVATE_KEY` in `.env`

### "Transaction reverted"
- Increase `MAX_SLIPPAGE_PERCENT` in config
- Check token liquidity on Base

---

## Links

| Resource | URL |
|----------|-----|
| Base Network | https://base.org |
| Base Bridge | https://bridge.base.org |
| BaseScan | https://basescan.org |
| Uniswap on Base | https://app.uniswap.org |
| ASIG Token | https://basescan.org/token/0x30610a21764bb38c43a2e532cfba91c9db927994 |
| Base Faucet (Sepolia) | https://www.coinbase.com/faucets/base-ethereum-goerli-faucet |
