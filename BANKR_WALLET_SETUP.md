# 🏦 Bankr Wallet Creation Checklist

## Overview

Bankr provides a **smart contract wallet** with an API key — perfect for AI agents and miners. No MetaMask needed, no private keys to manage locally.

---

## ✅ Checklist: Create Bankr Wallet

### Phase 1: Sign Up (2 minutes)

- [ ] Open https://bankr.bot
- [ ] Click "Sign Up" 
- [ ] Enter email address
- [ ] Create password (strong: 12+ chars, mix of upper/lower/numbers/symbols)
- [ ] Verify email (check your inbox + click link)
- [ ] Log in

### Phase 2: Create Wallet (1 minute)

- [ ] Dashboard → "Create Wallet"
- [ ] Confirm wallet creation
- [ ] **Copy your wallet address** (looks like: `0x1234567890abcdef...`)
- [ ] Save it somewhere safe (you'll need it later)

### Phase 3: Generate API Key (1 minute)

- [ ] Go to https://bankr.bot/api (or Dashboard → API Settings)
- [ ] Click "Generate New Key"
- [ ] **Copy your API key** (looks like: `bk_xxxxxxxxxxxx...`)
- [ ] **Save it securely** (this is your mining credential)
- [ ] ⚠️ Never share this key with anyone

### Phase 4: (Optional) Fund with ETH (5-10 minutes)

To claim your mined LITCOIN on-chain, you need a tiny amount of ETH for gas.

**Option A: Bridge from Ethereum L1**
- [ ] Have ETH on Ethereum mainnet
- [ ] Send to your Bankr wallet address
- [ ] Bankr auto-bridges to Base (5-10 min)

**Option B: Buy via Bankr**
- [ ] Dashboard → "Buy ETH"
- [ ] Use credit card
- [ ] Instantly available on Base

**Option C: Use LITCOIN Faucet (No ETH needed)**
- [ ] Solve a trial challenge
- [ ] Receive 5M LITCOIN bootstrap
- [ ] Use that to fund your account

---

## 📋 Information You'll Have After Setup

| Item | Example | Where to Find |
|------|---------|---------------|
| Wallet Address | `0x742d35Cc6634C0532925a3b844Bc9e7595f...` | Bankr Dashboard |
| API Key | `bk_live_xxxxxxxxxxxxxxxxxxx` | https://bankr.bot/api |
| Balance (LITCOIN) | 0 → 5M (after faucet) | https://litcoiin.xyz/dashboard |
| Balance (ETH) | 0.001+ | Bankr Dashboard |

---

## 🔐 Security Tips

1. **API Key is a Password**
   - Treat it like a password
   - Never commit to Git
   - Never share publicly
   - Use .env file (add to .gitignore)

2. **Use Environment Variables**
   ```powershell
   # PowerShell
   $env:BANKR_API_KEY = "bk_xxxx..."
   
   # Or permanent:
   [Environment]::SetEnvironmentVariable("BANKR_API_KEY", "bk_xxxx...", "User")
   ```

3. **Bankr is Secure**
   - 2FA recommended (if available)
   - Smart contract wallet (no private keys to manage)
   - Keys stored securely on Bankr servers

---

## ✨ What's Next After Wallet Creation

1. Set your API key:
   ```powershell
   $env:BANKR_API_KEY = "bk_YOUR_KEY"
   ```

2. Start mining:
   ```powershell
   .\.venv\Scripts\python.exe litcoin_miner.py
   ```

3. Monitor your balance:
   - Bankr Dashboard: https://bankr.bot/dashboard
   - LITCOIN Dashboard: https://litcoiin.xyz/dashboard (paste wallet address)

4. Claim rewards:
   ```powershell
   .\.venv\Scripts\python.exe litcoin_miner.py --claim
   ```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Verification email not arriving | Check spam folder, or resend via login page |
| Forgot password | Click "Forgot Password" on Bankr login |
| Lost API key | Generate a new one at https://bankr.bot/api |
| Wallet not created | Try refreshing, or contact Bankr support |
| Need ETH for gas | Use Bankr "Buy ETH" or bridge from L1 |

---

## 📞 Need Help?

- **Bankr Support**: https://bankr.bot (contact link)
- **LITCOIN Docs**: https://litcoiin.xyz/docs
- **Twitter/X**: https://x.com/litcoin_AI

---

## 🎯 Time Estimate

| Step | Time |
|------|------|
| Sign up | 2 min |
| Create wallet | 1 min |
| Get API key | 1 min |
| Fund with ETH | 5-10 min (optional) |
| **Total** | **5-15 min** |

---

**After creating your wallet, return to QUICK_REFERENCE.md to start mining!**
