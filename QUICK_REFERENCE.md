# ⚡ AegisForge — Quick Reference

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Start paper trading engine
cd engine
python run_engine.py

# 4. Or start the FastAPI server
cd engine
python main_fastapi.py
```

---

## 📋 Trading Modes

| Mode | Risk | Capital | Config |
|------|------|---------|--------|
| **Paper** | None | $0 | `PAPER_MODE=true` |
| **Micro** | Low | $10–100 | `MICRO_MODE=true` |
| **Live** | High | $30K+ | `LIVE_MODE=true` + Binance keys |

---

## 🔑 Required Environment Variables

```env
# Trading mode
PAPER_MODE=true
MICRO_MODE=false

# Wallet (required for micro/live)
METAMASK_PRIVATE_KEY=0xYOUR_KEY
METAMASK_WALLET_ADDRESS=0xYOUR_ADDRESS
METAMASK_RPC_URL=https://mainnet.base.org
METAMASK_CHAIN_ID=8453

# AI chat (optional)
OPENAI_API_KEY=your-openrouter-or-openai-key

# Whale tracker (optional)
ETHERSCAN_API_KEY=your-key
BASESCAN_API_KEY=your-key
```

---

## 🤖 Strategies

8 built-in strategies in `engine/strategies/`:

| Strategy | File |
|----------|------|
| RSI | `rsi_strategy.py` |
| RSI Trend | `rsi_trend_strategy.py` |
| Bollinger Bands | `bollinger_strategy.py` |
| MACD | `macd_strategy.py` |
| Momentum | `momentum_strategy.py` |
| Breakout | `breakout_strategy.py` |
| Volume Spike | `volume_spike_strategy.py` |
| Aegis Fusion | `aegis_fusion_strategy.py` |

---

## 🌐 API Endpoints (FastAPI)

```bash
cd engine && python main_fastapi.py
# Server starts at http://localhost:8000
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server status |
| `/strategies` | GET | List strategies |
| `/strategy/toggle` | POST | Enable/disable strategy |
| `/performance` | GET | Performance summary |
| `/whale-alerts` | GET | Whale movements |
| `/chat` | POST | AI chat |

---

## 🔗 Deployed Contracts (Base Mainnet)

| Contract | Address |
|----------|---------|
| ASIG Token | `0x30610a21764bb38c43a2e532cfba91c9db927994` |
| SignalRegistry | `0xb5AFac365FD2968157EFF7183144e46F11772926` |

---

## 🛠️ Useful Commands

```bash
# Test on-chain data feed
cd engine && python test_data_feed.py

# Test micro trader (requires funded wallet)
cd engine && python test_micro_trader.py

# Run airdrop farmer (dry run by default)
cd airdrop-farmer && python farmer.py

# Build token allowlist
cd engine && python scripts/build_allowlist.py
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Failed to connect to RPC" | Check `METAMASK_RPC_URL` in `.env` |
| "Chain ID mismatch" | Set `METAMASK_CHAIN_ID=8453` for Base mainnet |
| "No private key" | Normal for paper mode; set key for micro/live |
| "Transaction reverted" | Check slippage settings or token liquidity |
| Import errors | Run from `engine/` directory |

---

## 📚 Documentation

- **SETUP_GUIDE.md** — Full setup walkthrough
- **docs/BLOCKCHAIN_SETUP.md** — Wallet and blockchain configuration
- **docs/TRADING_MODES.md** — Trading modes comparison
- **README.md** — Project overview and architecture

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Base Network | https://base.org |
| Base Bridge | https://bridge.base.org |
| BaseScan | https://basescan.org |
| Uniswap (Base) | https://app.uniswap.org |
| Base Sepolia Faucet | https://www.coinbase.com/faucets/base-ethereum-goerli-faucet |
