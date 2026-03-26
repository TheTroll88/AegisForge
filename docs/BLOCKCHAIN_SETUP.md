# 🔗 Blockchain & Wallet Setup Guide

## Overview

AegisForge trades on **Base** (an Ethereum L2 by Coinbase) using Uniswap V3 for on-chain swaps.
This guide covers wallet setup, funding, and connecting to the engine.

---

## Step 1: Get Your Wallet Private Key

### MetaMask

1. Open MetaMask
2. Click: **Settings → Security & Privacy**
3. Click: **Reveal Secret Recovery Phrase** or **Export Private Key**
4. Enter your password and copy your **private key**
   - ⚠️ **NEVER share this key with anyone. NEVER commit it to git.**

### Generate a New Wallet

```python
from eth_account import Account
acct = Account.create()
print("Address:", acct.address)
print("Key:", acct.key.hex())
```

---

## Step 2: Configure `.env`

Edit `.env` in the project root:

```env
# Wallet
METAMASK_PRIVATE_KEY=0xYOUR_64_CHAR_HEX_KEY
METAMASK_WALLET_ADDRESS=0xYOUR_WALLET_ADDRESS

# Base Mainnet
METAMASK_RPC_URL=https://mainnet.base.org
METAMASK_CHAIN_ID=8453

# Micro Trading Settings
MICRO_MODE=true
```

For **testnet** (safe for experimenting with no real funds):

```env
METAMASK_RPC_URL=https://sepolia.base.org
METAMASK_CHAIN_ID=84532
```

---

## Step 3: Fund Your Wallet

You need **ETH on Base** for gas fees and **USDC on Base** for trading.

### Via Bridge (Ethereum → Base)

1. Go to https://bridge.base.org
2. Connect MetaMask
3. Bridge ETH from Ethereum to Base mainnet
4. Minimum recommended: **$10–20 for initial testing**

### Via Coinbase (Direct to Base)

- Buy or withdraw ETH/USDC directly to the Base network from Coinbase

### Base Sepolia Testnet (No real funds)

- Get test ETH: https://www.coinbase.com/faucets/base-ethereum-goerli-faucet
- Use `METAMASK_CHAIN_ID=84532` and `METAMASK_RPC_URL=https://sepolia.base.org`

---

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages: `web3`, `eth-account`, `python-dotenv`

---

## Step 5: Test Your Connection

```bash
cd engine
python -c "
from core.wallet_manager import WalletManager
wallet = WalletManager()
balance = wallet.get_balance()
print(f'✅ Connected! ETH Balance: {balance}')
"
```

Expected output:
```
✅ Connected to chain ID: 8453
✅ Loaded account: 0x123...
💰 Native Balance: 0.123456
```

---

## Step 6: Start Micro Trading

```bash
cd engine
python test_micro_trader.py
```

Expected output:
```
✅ MicroTrader initialized
💰 ETH Balance: 0.05
✅ Buy executed: {...}
✅ Sell executed: {...}
```

---

## Trading Flow

```
Signal Generated
    ↓
Calculate Position Size ($0.01 – $100)
    ↓
Build Uniswap V3 Swap Transaction
    ↓
Sign with Wallet Private Key
    ↓
Send to Base Network
    ↓
Wait for Confirmation (~2 seconds on Base)
    ↓
Log Trade
    ↓
Track Profit/Loss
```

---

## Cost Breakdown (Base)

| Operation | Gas | Approx Cost |
|-----------|-----|-------------|
| Token Swap | ~200k gas | $0.001–0.01 |
| Token Approval | ~50k gas | $0.0002–0.003 |
| **Total per trade** | | **~$0.001–0.01** |

Base gas fees are significantly cheaper than Ethereum mainnet.

---

## Safety Checklist

✅ Test with $1 trades first  
✅ Start with `MICRO_MODE=true` in paper mode first  
✅ Keep private key in `.env` — never commit to git  
✅ Verify all TX hashes on BaseScan  
✅ Monitor gas prices before large trades  

---

## Verify Trades on BaseScan

View all your transactions:
- **BaseScan**: https://basescan.org/address/YOUR_ADDRESS

---

## Troubleshooting

### ❌ "Failed to connect to RPC"
- Check internet connection
- Try public fallback: `https://mainnet.base.org`

### ❌ "Chain ID mismatch"
- Ensure `METAMASK_CHAIN_ID` matches the RPC endpoint
- Base mainnet = 8453, Base Sepolia = 84532

### ❌ "Insufficient balance for gas"
- Need ETH on Base for gas fees
- Bridge ETH from Ethereum at https://bridge.base.org

### ❌ "Transaction reverted"
- Increase slippage tolerance
- Check token liquidity on https://app.uniswap.org

---

## Deployed Contracts (Base Mainnet)

| Contract | Address |
|----------|---------|
| ASIG Token | `0x30610a21764bb38c43a2e532cfba91c9db927994` |
| SignalRegistry | `0xb5AFac365FD2968157EFF7183144e46F11772926` |

These contracts are integrated via `engine/core/asig_bridge.py`.
