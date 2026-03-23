# AegisForge

An AI-driven, all-in-one financial platform. Trading, mining, farming, security — automated and accessible to everyone regardless of experience level.

**Token**: [AegisSignal (ASIG)](https://aegissignal.io) on Base chain — the community token powering the AegisForge ecosystem.

## Vision

Most AI trading platforms gatekeep features behind premium tiers and charge people who don't know any better. AegisForge is the opposite: one quality level for everyone, low-cost access, and AI that does the heavy lifting so someone with zero crypto knowledge can participate on equal footing.

The bots make money. The users benefit. Nobody gets a watered-down version.

No third-party API key reselling. No rebranding someone else's infrastructure. If AegisForge needs AI, it runs its own models and generates its own keys.

## Architecture

```
AegisForge/
├── airdrop-farmer/            # DEX swap farmer (Base chain)
│   └── farmer.py
├── secure_vault.ps1           # Windows DPAPI credential vault
├── phaseport/                 # Data migration and continuity layer
│   ├── PhasePort_Adapter.py   # Module orchestration GUI
│   ├── activate_member.py     # Module activation CLI
│   └── memory_logger.py       # State checkpoint and memory tracking
├── council/                   # AI agent modules (early-stage, experimental)
│   ├── members/               # Agent role configs (JSON)
│   └── functions/             # Agent task scripts (Python)
├── tools/                     # Standalone open-source utilities (MIT)
│   ├── auto_organizer.py      # File sorting daemon with MD5 dedup
│   ├── manage_organizer.ps1   # Organizer start/stop/install management
│   ├── ocr_pipeline.py        # Screenshot OCR recovery tool
│   └── forensic_sweep.py      # Full-drive forensic scanner
├── legacy/                    # Archived earlier iterations (reference only)
│   ├── aegis_core/            # Founding project docs and declarations
│   └── trading-engine-v1/     # Original trading bot prototype source
└── logs/                      # Runtime logs (gitignored)
```

## Current State

| Component | Status | Description |
|-----------|--------|-------------|
| **Airdrop Farmer** | Ready | DEX swaps on Base (DRY_RUN default) |
| **Secure Vault** | Active | Windows DPAPI encrypted credential storage |
| **Data Continuity** | Ready | Migration layer and state checkpointing |
| **AI Agents** | Experimental | Modular task agents — pattern recognition, research, monitoring |
| **Tools** | Active | Standalone utilities — file organizer, OCR pipeline, forensic scanner |

## Planned Features

- [ ] AI trading engine — same quality for all users, no tier levels
- [ ] Free paper trading — see real results with simulated funds before risking anything
- [ ] **AI penetration testing bot** — autonomous ethical hacker, sellable standalone to companies
  - Self-learning agent that probes systems from every angle (inside and outside)
  - Finds vulnerabilities, logs exactly how it got in, reports to the security team
  - Never exploits, never corrupts — observe, document, report
  - Thinks freely, adapts approaches, tests what a real attacker would try
- [ ] ASIG token integration — faucet rewards, ecosystem participation, on-chain utility
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
- [ ] Automated contract auditing
- [ ] AI assistant for zero-knowledge users
- [ ] Self-hosted model infrastructure — no third-party API key reselling
- [ ] Stock market integration (phase 2)
- [ ] Background AI agents for specialized tasks (trading, security, research)

## Philosophy

> "If it works for me and gets me out of my hole, there's another dude sitting behind a screen looking for a way out. And if I can give that to him, that's the payment."

This project exists because the AI finance space is full of greed. Premium tiers for the same bot. Paywalled paper trading. Features locked behind subscriptions that cost more than most people can afford.

AegisForge is built on the principle that if the AI is good enough, it pays for itself — for the creator and the users. No one gets a lesser version. The bots work for everyone equally.

If a trading bot hits 65% success rate, every single user gets that 65%. Period.

## License

[MIT](LICENSE) — Copyright (c) 2025-2026 Nathaniel Crigger
