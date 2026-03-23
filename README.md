# AegisForge

An AI-driven, all-in-one financial platform. Trading, mining, farming, security — automated and accessible to everyone regardless of experience level.

## Vision

Most AI trading platforms gatekeep features behind premium tiers and charge people who don't know any better. AegisForge is the opposite: one quality level for everyone, low-cost access, and AI that does the heavy lifting so someone with zero crypto knowledge can participate on equal footing.

The bots make money. The users benefit. Nobody gets a watered-down version.

No third-party API key reselling. No rebranding someone else's infrastructure. If AegisForge needs AI, it runs its own models and generates its own keys.

## Architecture

```
AegisForge/
├── airdrop-farmer/            # Aerodrome DEX swap farmer (Base chain)
│   └── farmer.py
├── secure_vault.ps1           # Windows DPAPI credential vault
├── phaseport/                 # Data migration and continuity layer
│   ├── PhasePort_Adapter.py   # GUI launcher
│   ├── activate_member.py     # Module activation CLI
│   └── memory_logger.py       # State checkpoint and memory tracking
├── ocr_pipeline.py            # Screenshot OCR recovery tool
├── forensic_sweep.py          # Full-drive forensic scanner
├── auto_organizer.py          # File sorting daemon with MD5 dedup
├── manage_organizer.ps1       # Organizer start/stop/install management
├── council/                   # AI agent concepts (early-stage, experimental)
│   ├── members/               # Agent profile configs (JSON)
│   └── functions/             # Agent activation scripts (Python)
├── legacy/                    # Archived earlier iterations (reference only)
│   ├── aegis_core/            # Original Aegis declarations and protocols
│   ├── kratos_archive/        # Original Kratos trading bot source
│   └── bridge_terminal/       # VPS bridge terminal script
└── logs/                      # Runtime logs (gitignored)
```

## Current State

| Component | Status | Description |
|-----------|--------|-------------|
| **Airdrop Farmer** | Ready | Aerodrome DEX swaps on Base (DRY_RUN default) |
| **Secure Vault** | Active | Windows DPAPI encrypted credential storage |
| **PhasePort** | Ready | Data continuity and migration layer |
| **Utilities** | Active | OCR pipeline, forensic sweep, file organizer |

## Planned Features

- [ ] AI trading bot engine (evolved from Kratos) — same quality for all users, no tier levels
- [ ] Free paper trading — see real results with fake money before risking anything
- [ ] Security vulnerability scanner — 24/7 automated detection, sellable standalone to companies
- [ ] Custom blockchain miners (original, not third-party)
- [ ] Multi-chain airdrop discovery
- [ ] AI-driven news, risk analysis, and token security checks
- [ ] Automated contract auditing (replace manual DexScreener lookups)
- [ ] AI assistant for zero-knowledge users
- [ ] Self-hosted API key generation — no OpenAI/third-party key reselling
- [ ] Stock market integration (phase 2)
- [ ] Background AI agents for specialized tasks (trading, security, research)

## Philosophy

> "If it works for me and gets me out of my hole, there's another dude sitting behind a screen looking for a way out. And if I can give that to him, that's the payment."

This project exists because the AI finance space is full of greed. Premium tiers for the same bot. Paywalled paper trading. Features locked behind subscriptions that cost more than most people can afford.

AegisForge is built on the principle that if the AI is good enough, it pays for itself — for the creator and the users. No one gets a lesser version. The bots work for everyone equally.

If a trading bot hits 65% success rate, every single user gets that 65%. Period.

## License

[MIT](LICENSE) — Copyright (c) 2025-2026 Nathaniel Crigger

---

**Status**: ✅ Ready to mine (after Bankr wallet + API key configuration)
