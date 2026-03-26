# 🤖 Trading Modes — Comparison & Quick Start

## Three Trading Modes

### 1. 📊 PAPER TRADING (Recommended: Start Here)
**Risk**: None | **Cost**: Free | **Speed**: Instant

```env
# In .env:
PAPER_MODE=true
MICRO_MODE=false
```

**Use case**:
- Test strategies without any risk
- Verify signals are working correctly
- Practice for 7–14 days before committing real funds

**Behavior**: All trades simulated with a virtual $10,000 balance. No gas fees, no slippage.

---

### 2. 💵 MICRO TRADING (Recommended: Next Step)
**Risk**: Low | **Cost**: ~$0.001–0.01/trade (gas) | **Speed**: ~2 seconds on Base

```env
# In .env:
PAPER_MODE=false
MICRO_MODE=true

METAMASK_PRIVATE_KEY=0xYOUR_KEY
METAMASK_WALLET_ADDRESS=0xYOUR_ADDRESS
METAMASK_RPC_URL=https://mainnet.base.org
METAMASK_CHAIN_ID=8453
```

**Use case**:
- See real profit/loss at small scale
- Test on actual Base blockchain
- Learn gas fees and slippage dynamics
- Build confidence before scaling up

**What happens**:
1. Each trade costs a tiny gas fee on Base (~$0.001–0.01)
2. You gain/lose the actual swing amount in USDC
3. All P&L tracked in logs/trade_log.json
4. Position size scales with your configured balance

**Capital needed**: $10–20 (covers gas + small trading buffer)

---

### 3. 🚀 LIVE TRADING (After proven success)
**Risk**: High | **Cost**: ~0.1% fee per trade | **Speed**: ~2 seconds

```env
# In .env:
PAPER_MODE=false
MICRO_MODE=false
LIVE_MODE=true

BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

**Use case**:
- Trade with your full capital on Binance
- Only after 4+ weeks of consistent micro trading results

---

## Quick Start: Paper → Micro → Live

### ✅ Phase 1: Paper Trading (Week 1)

```bash
# Start the trading engine
cd engine
python run_engine.py

# Or start the FastAPI server
cd engine
python main_fastapi.py
```

**Check**:
- ✅ Strategies generating signals
- ✅ Trades logging to `logs/trade_log.json`
- ✅ Win rate printed in console

**Goal**: 60%+ win rate on paper for 50+ trades

---

### 💵 Phase 2: Micro Trading (Week 2–4)

**1. Set up wallet**
See [BLOCKCHAIN_SETUP.md](BLOCKCHAIN_SETUP.md) for detailed instructions.

**2. Fund your wallet**
- Bridge ETH to Base: https://bridge.base.org
- Get ~$15 USDC on Base
- Keep a small ETH balance for gas

**3. Update configuration**

```env
METAMASK_PRIVATE_KEY=0xYOUR_KEY
METAMASK_WALLET_ADDRESS=0xYOUR_ADDRESS
METAMASK_RPC_URL=https://mainnet.base.org
METAMASK_CHAIN_ID=8453
MICRO_MODE=true
```

**4. Run test**

```bash
cd engine
python test_micro_trader.py
```

**5. Monitor trades**
- Check `logs/trade_log.json`
- View on blockchain: https://basescan.org/address/YOUR_ADDRESS

**Goals**:
- Complete 50+ micro trades
- Win rate stays above 60%
- Total P&L is positive
- Understand gas fee impact

---

### 🚀 Phase 3: Live Trading (After 4 weeks micro success)

**Only proceed if**:
- ✅ Win rate consistently > 60% on micro for 4+ weeks
- ✅ Total micro P&L is positive
- ✅ Comfortable with trade execution and delays

**1. Get Binance API Keys**
- Go to: https://www.binance.com/en/my/settings/api-management
- Create API key (enable Spot trading)
- Restrict by IP for security

**2. Add to `.env`**

```env
LIVE_MODE=true
MICRO_MODE=false
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

**3. Update position sizing in `engine/core/config.py`**

```python
POSITION_SIZE_PERCENT = 0.5  # 0.5% per trade
MICRO_MODE = False
LIVE_MODE = True
```

---

## How to Switch Modes

### Paper → Micro

```python
# In engine/core/config.py:
PAPER_MODE = False
MICRO_MODE = True
```

Then restart the engine.

---

### Micro → Live

```python
# In engine/core/config.py:
MICRO_MODE = False
LIVE_MODE = True
```

Then restart with Binance API keys in `.env`.

---

## Risk Levels

```
Paper Trading:   ✅ (No risk, test signals)
Micro Trading:   ⚠️  (Low risk, real on-chain P&L)
Live Trading:    🔥 (High risk, full capital)
```

**Recommended Path**:
1. **Paper**: 7 days (free, verify signals work)
2. **Micro**: 28 days (low cost, real outcomes)
3. **Live**: Scaled approach, start small

---

## Key Metrics to Track

| Metric | Paper | Micro | Live |
|--------|-------|-------|------|
| Win Rate Target | 65%+ | 60%+ | 60%+ |
| Win/Loss Ratio | > 1.5× | > 1.2× | > 1.1× |
| Max Consecutive Losses | < 5 | < 5 | < 10 |

---

## Emergency Stop

```python
# In engine/core/config.py:
KILL_SWITCH = True  # Stops all trades immediately

# Or set via .env:
MICRO_MODE=false
LIVE_MODE=false
```
