# Legacy Code Archive

This folder contains earlier iterations and archived code from the project's history.
These files are preserved for reference and learning.

**This is NOT part of the active application.** It documents where the project started.

## Contents

### `aegis_core/`
Original project declarations and design documents from early 2025. Includes the founding mission statement, sovereignty markers, and restoration protocols that defined the project's direction.

### `trading-engine-v1/`
Complete source of the original trading engine prototype. Includes momentum-based strategy, sandbox/live execution modes, exchange client integration, and an automated watchdog process. This is the ancestor of the current trading system being developed for AegisForge.

**If you're reading this code:**
- It requires a `config.json` with `mode` set to `sandbox` or `live` — no example config is included, so check the source for expected keys.
- The trading pair is hardcoded to BTCUSDT in the exchange client. Change it in the BinanceClient class if you need other pairs.
- The main loop catches exceptions and continues — if something breaks, check the logs rather than waiting for a crash.
- Dependencies: `python-binance`, `python-dotenv`, plus any custom strategy modules referenced in the config.
- This is archived reference code, not a runnable application. Use it to understand the architecture, not to deploy.
