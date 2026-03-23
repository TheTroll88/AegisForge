# AegisForge

An AI-driven, all-in-one financial platform. Trading, mining, farming, security — automated and accessible to everyone regardless of experience level.

## Vision

Most AI trading platforms gatekeep features behind premium tiers and charge people who don't know any better. AegisForge is the opposite: one quality level for everyone, low-cost access, and AI that does the heavy lifting so someone with zero crypto knowledge can participate on equal footing.

The bots make money. The users benefit. Nobody gets a watered-down version.

## Architecture

```
AegisForge/
├── litcoin_miner.py          # AI-powered blockchain miner
├── miner_daemon.ps1           # Background supervisor with auto-restart and auto-claim
├── ensure_daemon.ps1          # Startup helper for the daemon
├── secure_vault.ps1           # Windows DPAPI credential vault
├── airdrop-farmer/            # Aerodrome DEX swap farmer (Base chain)
│   └── farmer.py
├── council/                   # Council of 14 — specialized AI worker modules
│   ├── members/               # 14 member profile configs (JSON)
│   └── functions/             # 14 member activation scripts (Python)
├── phaseport/                 # Data migration and continuity layer
│   ├── PhasePort_Adapter.py   # GUI launcher for council members
│   ├── activate_member.py     # CLI council member activation
│   └── memory_logger.py       # State checkpoint and memory tracking
├── dashboard_mirror.py        # Local dashboard health snapshot
├── bankr_mirror.py            # Bankr API earnings mirror
├── ocr_pipeline.py            # Screenshot OCR recovery tool
├── forensic_sweep.py          # Full-drive forensic scanner
├── auto_organizer.py          # File sorting daemon with MD5 dedup
├── manage_organizer.ps1       # Organizer start/stop/install management
├── legacy/                    # Archived earlier iterations (reference only)
│   ├── aegis_core/            # Original Aegis declarations and protocols
│   ├── kratos_archive/        # Original Kratos trading bot source
│   └── bridge_terminal/       # VPS bridge terminal script
├── reports/                   # Generated analysis reports
└── logs/                      # Runtime logs (gitignored)
```

## Active Components

| Component | Status | Description |
|-----------|--------|-------------|
| **LITCOIN Miner** | Running | AI comprehension/research mining with auto-claim |
| **Miner Daemon** | Running | Supervisor with heartbeat monitoring, crash recovery, 30-min claim cycle |
| **Airdrop Farmer** | Ready | Aerodrome DEX swaps on Base (DRY_RUN default) |
| **Council of 14** | Configured | 14 specialized AI modules with activation scripts |
| **PhasePort** | Ready | Data continuity and migration layer |
| **Secure Vault** | Active | Windows DPAPI encrypted credential storage |

## Planned Features

- [ ] AI trading bot engine (evolved from Kratos) — same quality for all users
- [ ] Free paper trading — see real results with fake money before risking anything
- [ ] Security vulnerability scanner — 24/7 automated detection, sellable standalone
- [ ] Multi-chain mining expansion
- [ ] Multi-chain airdrop discovery
- [ ] AI-driven news and risk analysis
- [ ] Automated token security checks (replace manual DexScreener lookups)
- [ ] AI assistant for zero-knowledge users
- [ ] Stock market integration (phase 2)

## Quick Start

```bash
# Start the miner daemon (background supervisor)
powershell -File miner_daemon.ps1

# Run the miner directly
python litcoin_miner.py

# Check miner status
python litcoin_miner.py --status

# Claim rewards
python litcoin_miner.py --claim

# Research mining
python litcoin_miner.py --research

# Dashboard snapshot
python dashboard_mirror.py
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for full environment setup and [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for daily operations.

## Philosophy

> "If it works for me and gets me out of my hole, there's another dude sitting behind a screen looking for a way out. And if I can give that to him, that's the payment."

This project exists because the AI finance space is full of greed. Premium tiers for the same bot. Paywalled paper trading. Features locked behind subscriptions that cost more than most people can afford.

AegisForge is built on the principle that if the AI is good enough, it pays for itself — for the creator and the users. No one gets a lesser version.

## License

[MIT](LICENSE) — Copyright (c) 2025-2026 Nathaniel Crigger

---

**Status**: ✅ Ready to mine (after Bankr wallet + API key configuration)
