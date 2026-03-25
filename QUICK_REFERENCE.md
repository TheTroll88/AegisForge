# ⚡ LITCOIN Miner — Quick Reference Card

## 🚀 One-Minute Setup

```powershell
# 1. Set your Bankr API key (get it at bankr.bot/api)
$env:BANKR_API_KEY = "bk_YOUR_KEY"

# 2. Start mining
.\.venv\Scripts\python.exe litcoin_miner.py

# 3. Check rewards
.\.venv\Scripts\python.exe litcoin_miner.py --status

# 4. Claim on-chain
.\.venv\Scripts\python.exe litcoin_miner.py --claim
```

---

## 📋 What You Have Ready

✅ **Environment**
- Python 3.13.7 (virtual environment configured)
- All dependencies installed: litcoin, requests, websocket-client

✅ **Scripts**
- `litcoin_miner.py` — Full-featured standalone miner
- `run.bat` — Windows launcher (easier than command line)

✅ **Documentation**
- `SETUP_GUIDE.md` — Detailed walkthrough
- `README.md` — Project overview
- `.env.example` — Config template

---

## 🏦 Create Bankr Wallet (Required)

| Step | Action |
|------|--------|
| 1 | Go to https://bankr.bot |
| 2 | Sign up (email + password) |
| 3 | Create wallet (appears on Dashboard) |
| 4 | Get API key at https://bankr.bot/api |
| 5 | Copy your key: `bk_xxx...` |
| 6 | (Optional) Fund with ETH for gas |

**Takes: ~5 minutes**

---

## ⛏️ Mining Commands

### Comprehension Mining (No AI key needed)
```powershell
.\.venv\Scripts\python.exe litcoin_miner.py
```
Solves prose reasoning challenges. Earn LITCOIN for each correct answer.

### Research Mining (Requires AI key)
```powershell
$env:AI_API_KEY = "sk_YOUR_KEY"
.\.venv\Scripts\python.exe litcoin_miner.py --research
```
Solve real optimization problems. Quality-weighted rewards (up to 110× more for breakthroughs).

### Iterate on One Task (Karpathy-style)
```powershell
.\.venv\Scripts\python.exe litcoin_miner.py --loop --task=tokenizer-001 --rounds=50
```
Recommended approach — better rewards for focused iteration.

---

## 💰 Claiming Rewards

```powershell
# Check balance
.\.venv\Scripts\python.exe litcoin_miner.py --status

# Claim on-chain
.\.venv\Scripts\python.exe litcoin_miner.py --claim
```

Rewards accumulate at the coordinator, then you claim on-chain via Bankr (no ETH needed if using Bankr wallet).

---

## 🔌 Relay Mining (Earn 2× per AI request)

**Optional: Serve AI inference requests and earn extra LITCOIN**

```powershell
# Set your AI provider key
$env:AI_API_KEY = "sk_YOUR_OPENAI_KEY"

# Start mining (relay auto-starts)
.\.venv\Scripts\python.exe litcoin_miner.py
```

**Best providers:**
- **OpenRouter** (free tier): https://openrouter.ai
- **OpenAI**: https://platform.openai.com
- **Groq** (fastest): https://groq.com
- **Together AI**: https://together.ai
- **Local Ollama** (free, offline): https://ollama.ai

---

## 💾 Configuration Methods

### Method A: Environment Variables (Recommended)
```powershell
$env:BANKR_API_KEY = "bk_YOUR_KEY"
$env:AI_API_KEY = "sk_YOUR_KEY"
$env:MODEL = "gpt-4o-mini"
```

### Method B: Permanent (All Sessions)
```powershell
[Environment]::SetEnvironmentVariable("BANKR_API_KEY", "bk_YOUR_KEY", "User")
```
Restart PowerShell after.

### Method C: Direct Edit
Open `litcoin_miner.py`, update CONFIG dict.

---

## 📊 Monitoring

| Tool | URL/Command |
|------|-------------|
| Your Wallet (Bankr) | https://bankr.bot/dashboard |
| LITCOIN Dashboard | https://litcoiin.xyz/dashboard |
| LITCOIN Stats | https://litcoiin.xyz/stats |
| Research Lab | https://litcoiin.xyz/research |
| API Health | https://api.litcoiin.xyz/v1/health |

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "BANKR_KEY not configured" | Set env var: `$env:BANKR_API_KEY = "bk_..."` |
| "Connection refused" | Check internet, verify API online |
| "Relay not starting" | Verify AI_API_KEY is set and valid |
| Not earning rewards | Ensure Bankr key is correct (starts with `bk_`) |
| SDK import error | Reinstall: `.venv\Scripts\pip install --upgrade litcoin` |

---

## 🎯 Earnings Overview

| Mining Type | Requirement | Reward | Notes |
|-------------|-------------|--------|-------|
| **Comprehension** | Bankr API key | 10% of daily emission | No AI key needed |
| **Research** | AI API key | 65% of daily emission (quality-weighted) | Breakthroughs earn 110× more |
| **Staking** | Min 1M LITCOIN | 25% of daily emission + mining boost | Tiers reduce vault collateral |
| **Relay** | AI API key | 2× mining weight per request | Requires serving AI compute |

**Daily Emission**: ~1.5% of treasury (currently ~13.5M LITCOIN at 2B treasury)

---

## 📚 Documentation Files

- **SETUP_GUIDE.md** — Complete setup with Bankr wallet creation steps
- **README.md** — Project overview
- **litcoin_miner.py** — Fully commented source code
- **QUICK_REFERENCE.md** — This file

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| Bankr Signup | https://bankr.bot |
| API Keys | https://bankr.bot/api |
| Stats | https://litcoiin.xyz/stats |
| Docs | https://litcoiin.xyz/docs |
| Coordinator | https://api.litcoiin.xyz |
| PyPI SDK | https://pypi.org/project/litcoin/ |

---

## ✅ Your Status

| Item | Status |
|------|--------|
| Python 3.9+ | ✅ Python 3.13.7 |
| Virtual Env | ✅ Configured |
| SDK + Deps | ✅ Installed (litcoin, requests, websocket-client) |
| Miner Script | ✅ Ready (litcoin_miner.py) |
| Windows Launcher | ✅ Ready (run.bat) |
| Documentation | ✅ Complete (SETUP_GUIDE.md, README.md) |
| **Bankr Wallet** | ⏳ **TODO** |
| **API Key** | ⏳ **TODO** |

---

## 🚀 Next Steps

1. **Create Bankr wallet** → https://bankr.bot
2. **Get API key** → https://bankr.bot/api
3. **Set env variable** → `$env:BANKR_API_KEY = "bk_YOUR_KEY"`
4. **Start mining** → `.\.venv\Scripts\python.exe litcoin_miner.py`
5. **Monitor** → https://litcoiin.xyz/dashboard
6. **Claim** → `.\.venv\Scripts\python.exe litcoin_miner.py --claim`

**Total time to first mine: ~10 minutes**

---

**Happy mining! 🏆**
