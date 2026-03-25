# AegisForge — Project Instructions

## What This Is
AI-driven crypto trading platform. Low-cost access, one quality level for everyone, no third-party API key reselling. Bots make money, users benefit. Nobody gets a watered-down version.

AegisForge is the **product** — the trading engine, strategies, contracts, whale tracker, airdrop farmer. The Aegis safety protocol repo is the **heart** — the system identity, the NoiseAsset, the bridge architecture. They connect but are separate projects.

## Owner
Nathaniel Crigger — full authority. Full discretion granted to the lead architect (Copilot/Claude).

## Command Structure
- **Lead Architect: GitHub Copilot (Claude)** — sole interface the owner talks to
- Lead delegates to agents, makes architecture decisions, fills gaps without asking
- Agents share knowledge base, have specific specialties (dev team model)
- No ceremonies, no mythology. Build what works.

## Architecture

```
AegisForge/
├── engine/                    # Trading engine (FastAPI + strategies + on-chain execution)
│   ├── main_fastapi.py        # FastAPI server — strategy loop, chat, whale endpoints
│   ├── run_engine.py          # Standalone engine launcher (100 iterations, no server)
│   └── core/                  # Engine internals
│       ├── config.py           # Mode selection: PAPER/MICRO/LIVE + risk params
│       ├── trading_engine.py   # TradingEngine class — run loop
│       ├── paper_trade.py      # PaperTrader — simulated $10k balance
│       ├── micro_trader.py     # MicroTrader — real on-chain micro positions ($0.01-$100)
│       ├── live_data_feed.py   # On-chain price feed via Uniswap V3 quoter
│       ├── dex_trader.py       # DEXTrader — Uniswap V3 exactInputSingle swaps
│       ├── wallet_manager.py   # Web3 wallet — MetaMask/eth-account, multi-chain
│       ├── trade_logger.py     # CSV + JSON trade logging
│       ├── whale_tracker.py    # Multi-chain whale transfer monitor (SQLite)
│       └── strategies/         # 8 trading strategies
│           ├── rsi_strategy.py
│           ├── bollinger_strategy.py
│           ├── macd_strategy.py
│           ├── momentum_strategy.py
│           ├── breakout_strategy.py
│           ├── volume_spike_strategy.py
│           ├── aegis_fusion_strategy.py
│           └── rsi_trend_strategy.py
├── council/                   # AI agent council (stubs — rebuild planned)
│   ├── agents/                # 16 agent scripts + state configs
│   ├── memory/                # Agent state checkpointing
│   └── activate_agent.py      # Agent activation CLI
├── contracts/                 # Deployed Solidity contracts
│   ├── ASIGToken.sol          # ASIG token — 1M supply, ERC-20, on Base
│   └── SignalRegistry.sol     # On-chain signal broadcasting, on Base
├── airdrop-farmer/            # Standalone DEX swap farmer (Aerodrome, Base chain)
│   └── farmer.py              # DRY_RUN default, flip to live with env vars
├── tools/                     # Standalone MIT utilities
│   ├── auto_organizer.py      # File sorting daemon with MD5 dedup
│   ├── manage_organizer.ps1   # Organizer management (start/stop/install)
│   ├── ocr_pipeline.py        # Screenshot OCR recovery
│   └── forensic_sweep.py      # Full-drive forensic scanner
├── phaseport/                 # Legacy GUI launcher (path issues, needs fixing)
├── legacy/                    # Archived earlier iterations (reference only)
├── docs/                      # Setup guides
├── logs/                      # Runtime logs (gitignored)
└── secure_vault.ps1           # Windows DPAPI credential vault
```

## Current State (updated 2026-03-24)

| Component | Status | Notes |
|-----------|--------|-------|
| Trading Engine | **Working** | 8 strategies, paper mode functional, micro wired but untested |
| FastAPI Server | **Working** | Strategy management, chat, performance, whale endpoints |
| Whale Tracker | **Working** | Multi-chain SQLite monitor, not yet feeding into strategy weights |
| Smart Contracts | **Deployed** | ASIG + SignalRegistry on Base — not wired into engine |
| Airdrop Farmer | **Ready** | DRY_RUN default, standalone |
| Council Agents | **Stubs** | 16 agents, all symbolic — rebuild planned |
| Micro Trading | **Untested** | Needs funded wallet + .env |
| Live Trading | **Not integrated** | Needs Binance keys |

## Deployed Contracts (Base chain)
- ASIG Token: `0x30610a21764bb38c43a2e532cfba91c9db927994`
- SignalRegistry: `0xb5AFac365FD2968157EFF7183144e46F11772926`

## Configuration
- Default mode: MICRO_MODE=True in config.py (but no wallet funded)
- Strategies auto-discover from engine/strategies/*.py via importlib
- LiveDataFeed uses on-chain Uniswap V3 quoter (not centralized API)
- .env not present in workspace — see .env.example or docs for required vars

## Conventions
- engine/ code uses relative imports from `core.*`
- run_engine.py runs from engine/ directory (cwd matters for imports)
- main_fastapi.py also runs from engine/ directory
- Strategies must expose a class ending in `Strategy` with an `evaluate(data)` method
- All logs go to logs/ (gitignored)
- GitHub repo is ONLY for the shipped app — dev tools, session logs, bootstrap scripts stay gitignored
- No hardcoded absolute paths in production code

## Known Issues to Fix
1. trade_logger.py — hardcoded path to old PhasePort project, must use relative AegisForge paths
2. wallet_manager.py — tx_receipt_log references old kratos_core path
3. main_fastapi.py strategy_loop() — indentation error in the inner for loop
4. Whale tracker signals not feeding into strategy weight adjustments
5. Council agents are all stubs — need real decision logic or removal

## Build Philosophy
- No shortcuts. No placeholder code. Production-grade from commit one.
- Build for expansion — architecture must accept growth without rewrites.
- Security is not optional — impenetrable by design.
- If there's only one right way, that's the way we build it.
- The system must not fail. Build it so it CAN'T fail.

## Relationship to Aegis
AegisForge is the product that users interact with. The Aegis safety protocol is the identity layer — the NoiseAsset, the bridges, the heart. They will connect via the bridge architecture (Phase 3 in Aegis build plan). For now they are separate repos.

## What NOT to Do
- Don't add dev tools or session management to the public repo
- Don't create documentation files unless asked
- Don't modify strategies without backing up first
- Don't commit .env files or credentials
- Don't add features beyond what's requested
