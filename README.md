# AegisForge

Low-cost AI-driven crypto trading. Paper trading with real results. Smart wallet with auto-bridging and gas abstraction. AI airdrop finder. Self-hosted AI — no third-party API key reselling. [ASIG token](https://aegissignal.io) on Base chain. Stock market integration planned.

## Vision

Most AI trading platforms gatekeep features behind premium tiers and charge people who don't know any better. AegisForge is the opposite: one quality level for everyone, low-cost access, and AI that does the heavy lifting so someone with zero crypto knowledge can participate on equal footing.

The bots make money. The users benefit. Nobody gets a watered-down version.

No third-party API key reselling. No rebranding someone else's infrastructure. If AegisForge needs AI, it runs its own models and generates its own keys.

## Architecture

```
AegisForge/
├── engine/                    # AI trading engine (Base chain, Uniswap V3)
│   ├── core/                  # Config, wallet, DEX, logging, data feeds
│   ├── strategies/            # 8 trading strategies (RSI, MACD, Bollinger, etc.)
│   ├── scripts/               # Utilities — allowlist builder, TX monitor, diagnostics
│   ├── data/                  # Token lists, allowlists, caches
│   ├── main_fastapi.py        # FastAPI server
│   └── run_engine.py          # Engine launcher
├── council/                   # AI agent council (variable agent count)
│   ├── agents/                # Agent scripts + state configs
│   ├── memory/                # State checkpointing and memory tracking
│   └── activate_agent.py      # Agent activation CLI
├── contracts/                 # Solidity smart contracts
│   ├── ASIGToken.sol          # ASIG token (1M supply, ERC-20)
│   └── SignalRegistry.sol     # On-chain signal broadcasting
├── airdrop-farmer/            # DEX swap farmer (Base chain)
│   └── farmer.py
├── secure_vault.ps1           # Windows DPAPI credential vault
├── tools/                     # Standalone open-source utilities (MIT)
│   ├── auto_organizer.py      # File sorting daemon with MD5 dedup
│   ├── manage_organizer.ps1   # Organizer start/stop/install management
│   ├── ocr_pipeline.py        # Screenshot OCR recovery tool
│   └── forensic_sweep.py      # Full-drive forensic scanner
├── docs/                      # Setup guides and reference
├── legacy/                    # Archived earlier iterations (reference only)
│   ├── aegis_core/            # Founding project docs
│   ├── trading-engine-v1/     # Original trading bot prototype
│   ├── safety-protocol/       # Early strategy experiments
│   └── expo-frontend/         # Incomplete mobile app scaffold
└── logs/                      # Runtime logs (gitignored)
```

## Current State

| Component | Status | Description |
|-----------|--------|-------------|
| **Trading Engine** | Active | 8 strategies, paper/micro/live modes, FastAPI server, Base chain DEX |
| **AI Council** | Experimental | Modular task agents — pattern recognition, research, monitoring |
| **Smart Contracts** | Deployed | ASIG token on Base, SignalRegistry for on-chain signals |
| **Airdrop Farmer** | Ready | DEX swaps on Base (DRY_RUN default) |
| **Secure Vault** | Active | Windows DPAPI encrypted credential storage |
| **Tools** | Active | Standalone utilities — file organizer, OCR pipeline, forensic scanner |
| **Whale Tracker** | Active | Multi-chain whale movement monitor with coordinated movement detection |

## Planned Features

- [x] AI trading engine — 8 strategies, paper/micro/live modes, FastAPI server
- [x] Paper trading — simulated funds with real market data
- [x] ASIG token — deployed on Base chain with on-chain signal broadcasting
- [ ] **Smart wallet** — multi-chain with automatic bridge detection and gas abstraction
  - Auto-detects chain mismatches and routes through bridges (no lost funds)
  - Validates destination wallet actually supports the target blockchain before sending
  - If no bridge exists and the destination can't receive it — transaction blocked, period
  - Gas fees deducted from the token being sent (no separate native token balance needed)
  - One-step sends: "send X tokens to this address" and it just works
  - Account abstraction (ERC-4337) + paymaster for gasless UX
- [ ] Custom blockchain miners (original, not third-party)
- [ ] Multi-chain airdrop discovery
- [ ] AI-driven news, risk analysis, and token security checks
- [x] **Whale tracker** — multi-chain large transfer monitoring (Ethereum, Base, BSC)
- [ ] Automated contract auditing
- [ ] AI assistant for zero-knowledge users
- [ ] Self-hosted model infrastructure — no third-party API key reselling
- [ ] Stock market integration (phase 2)
- [ ] Background AI agents for specialized tasks (trading, research, monitoring)

## Philosophy

> "If it works for me and gets me out of my hole, there's another dude sitting behind a screen looking for a way out. And if I can give that to him, that's the payment."

This project exists because the AI finance space is full of greed. Premium tiers for the same bot. Features locked behind subscriptions that cost more than most people can afford.

AegisForge is built on one principle: every user gets the same quality. No watered-down free tier, no premium-only features. Low-cost access, one level of service, and bots that work for everyone equally.

If a trading bot hits 65% success rate, every single user gets that 65%. Period.

## License

[MIT](LICENSE) — Copyright (c) 2025-2026 Nathaniel Crigger
