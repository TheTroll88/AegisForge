# 🚀 LITCOIN Miner Setup Guide

## Prerequisites Checklist

✅ **Python 3.9+** — Already installed (3.13.7)  
✅ **Virtual Environment** — Already configured (.venv)  
✅ **Dependencies** — Already installed (litcoin, requests, websocket-client)  
⏳ **Bankr Wallet** — See below  

---

## Step 1: Create a Bankr Wallet (Required)

### What is Bankr?
Bankr provides a smart contract wallet with an API key — perfect for LITCOIN mining. No MetaMask needed, no private keys to manage locally.

### Create Your Wallet

1. **Go to Bankr**
   ```
   https://bankr.bot
   ```

2. **Sign Up**
   - Create an account (email + password)
   - Verify your email

3. **Create a Wallet**
   - Go to Dashboard
   - Click "Create Wallet"
   - Your wallet address appears (e.g., `0x123abc...`)
   - Note it down — you'll need this for the LITCOIN dashboard

4. **Generate API Key**
   - Go to API Settings: https://bankr.bot/api
   - Click "Generate New Key"
   - Copy your Bankr API key: `bk_xxx...`
   - **Save this securely** — it's your mining credential

### Fund Your Wallet (Needed for Gas)

To claim rewards on-chain, you need a small amount of ETH for gas fees on Base.

**Option A: Bridge from L1**
- Send ETH to your Bankr wallet address on Ethereum L1
- Bankr auto-bridges to Base mainnet (~5 minutes)

**Option B: Buy on Bankr**
- In Bankr Dashboard, click "Buy ETH"
- Use a credit card (small fee)
- Instantly available on Base

**Option C: Use Faucet (Bootstrap)**
- New miners with zero balance can use the LITCOIN faucet
- Solve a trial challenge → receive 5M LITCOIN
- No gas needed to bootstrap
- See LITCOIN Faucet section for details

---

## Step 2: Configure Your Miner

### Method A: Environment Variables (Recommended)

**PowerShell:**
```powershell
$env:BANKR_API_KEY = "bk_YOUR_KEY"
$env:AI_API_KEY = "sk_YOUR_KEY"  # Optional: for relay mining
$env:MODEL = "gpt-4o-mini"
```

**Permanent (all future sessions):**
```powershell
[Environment]::SetEnvironmentVariable("BANKR_API_KEY", "bk_YOUR_KEY", "User")
```

### Method B: Direct in Script

Edit `litcoin_miner.py`, find the CONFIG section:
```python
CONFIG = {
    "BANKR_KEY": "bk_YOUR_KEY",        # ← Paste here
    "AI_API_KEY": "sk_YOUR_KEY",       # Optional
    "AI_URL": "...",
    "MODEL": "gpt-4o-mini",
}
```

### Method C: Copy `.env.example` to `.env`

```powershell
Copy-Item .env.example .env
# Edit .env with your keys
```

---

## Step 3: Verify Installation

Run a quick test:

```powershell
.\.venv\Scripts\python.exe -c "from litcoin import Agent; print('✅ litcoin SDK installed')"
```

Expected output:
```
✅ litcoin SDK installed
```

---

## Step 4: Start Mining

### Comprehension Mining (Default)

Mine without needing an AI key:
```powershell
.\.venv\Scripts\python.exe litcoin_miner.py
```

Runs 10 rounds by default. Each round:
1. Fetches a prose reasoning challenge
2. Solves it deterministically (no LLM calls)
3. Submits artifact and checksum
4. Earns LITCOIN if correct

### Research Mining (Requires AI Key)

Solve real optimization problems:
```powershell
.\.venv\Scripts\python.exe litcoin_miner.py --research
```

### Iterate on a Task (Recommended)

Karpathy-style iterations on one task earn better rewards:
```powershell
.\.venv\Scripts\python.exe litcoin_miner.py --loop --task=tokenizer-001 --rounds=50
```

### Check Your Balance

View earnings and claimable rewards:
```powershell
.\.venv\Scripts\python.exe litcoin_miner.py --status
```

### Claim Rewards On-Chain

```powershell
.\.venv\Scripts\python.exe litcoin_miner.py --claim
```

What happens:
1. Miner checks your claimable balance at the coordinator
2. Gets a claim signature
3. Submits on-chain via Bankr (no ETH needed if using Bankr wallet)
4. Rewards appear in your Bankr wallet on Base

---

## Step 5: Relay Mining (Optional)

If you provide an AI key, your miner automatically becomes a relay provider.

**Set your AI key:**
```powershell
$env:AI_API_KEY = "sk_YOUR_OPENAI_KEY"  # or any OpenAI-compatible key
```

**Verify relay is running:**
```powershell
.\.venv\Scripts\python.exe litcoin_miner.py --status
```

Look for `"relay": true` in the output.

**Earn from relay:**
- Every AI inference request you serve: **2× mining reward**
- Daily budget: 1M tokens/day (default)
- Quality score: starts at 1.0, improves with successful completions

---

## AI Provider Options

Use any OpenAI-compatible provider:

| Provider | URL | Free Tier | Recommended |
|----------|-----|-----------|-------------|
| **OpenRouter** | https://openrouter.ai/api/v1 | Yes (free tier) | ✅ Yes |
| **OpenAI** | https://api.openai.com/v1 | No (paid) | For GPT-4o |
| **Groq** | https://api.groq.com/openai/v1 | Yes (very fast) | For speed |
| **Together AI** | https://api.together.xyz/v1 | Yes | Good for research |
| **Bankr LLM Gateway** | Bankr Dashboard | Via credits | Integrated |
| **Local Ollama** | http://localhost:11434/v1 | Yes (offline) | Privacy + cost |

### OpenRouter Example (Recommended)

1. Sign up: https://openrouter.ai
2. Create API key: https://openrouter.ai/keys
3. Set it:
   ```powershell
   $env:AI_API_KEY = "sk_or_XXXX..."
   $env:AI_URL = "https://openrouter.ai/api/v1"
   $env:MODEL = "openrouter/auto"  # or "anthropic/claude-opus"
   ```

---

## Quick Command Reference

```powershell
# Comprehension mining
.\.venv\Scripts\python.exe litcoin_miner.py

# Research mining (single task)
.\.venv\Scripts\python.exe litcoin_miner.py --research

# Research mining (iterate on tokenizer-001)
.\.venv\Scripts\python.exe litcoin_miner.py --loop --task=tokenizer-001 --rounds=50

# Check status
.\.venv\Scripts\python.exe litcoin_miner.py --status

# Claim rewards
.\.venv\Scripts\python.exe litcoin_miner.py --claim

# Help
.\.venv\Scripts\python.exe litcoin_miner.py --help
```

---

## Dashboard & Monitoring

### Check Your Wallet

1. **Bankr Dashboard**: https://bankr.bot
   - View your wallet address
   - Check LITCOIN balance
   - Manage API keys

2. **LITCOIN Dashboard**: https://litcoiin.xyz/dashboard
   - Paste your wallet address
   - View earnings by source (mining, research, staking, relay)
   - See recent mining rounds

3. **Coordinator API**:
   ```powershell
   $wallet = "0xYOUR_WALLET"
   curl "https://api.litcoiin.xyz/v1/claims/status?wallet=$wallet"
   ```

---

## Troubleshooting

### "BANKR_KEY not configured"
```powershell
# Set environment variable
$env:BANKR_API_KEY = "bk_YOUR_KEY"

# Or edit litcoin_miner.py CONFIG section directly
```

### "Connection refused" / "API unreachable"
- Check internet connection
- Verify coordinator is online: `curl https://api.litcoiin.xyz/v1/health`

### "Relay not starting"
- Verify AI_API_KEY is set: `echo $env:AI_API_KEY`
- Check AI provider is responsive
- Relay is optional — comprehension mining works without it

### "Not earning rewards"
- Ensure Bankr key is correct (starts with `bk_`)
- Check coordinator API status
- Monitor your submissions: `python litcoin_miner.py --status`

### Upgrade litcoin SDK
```powershell
.\.venv\Scripts\pip.exe install --upgrade litcoin
```

---

## Links

| Resource | URL |
|----------|-----|
| Bankr Signup | https://bankr.bot |
| Bankr API Keys | https://bankr.bot/api |
| LITCOIN Dashboard | https://litcoiin.xyz/dashboard |
| LITCOIN Stats | https://litcoiin.xyz/stats |
| LITCOIN Research Lab | https://litcoiin.xyz/research |
| Coordinator API Docs | https://api.litcoiin.xyz |
| Python SDK (PyPI) | https://pypi.org/project/litcoin/ |
| Base Network | https://base.org |
| BaseScan | https://basescan.org |

---

## Next Steps

1. ✅ Create Bankr wallet (Step 1)
2. ✅ Configure miner (Step 2)
3. ✅ Verify installation (Step 3)
4. 🚀 **Start mining** (Step 4)
5. 💰 Claim rewards regularly
6. (Optional) Set up AI key for relay mining + research

---

## Support

- **LITCOIN Docs**: https://litcoiin.xyz/docs
- **Twitter/X**: https://x.com/litcoin_AI
- **Coordinator API**: https://api.litcoiin.xyz/docs
- **Issues**: GitHub or Discord (if available)

---

**Happy Mining! 🏆**
