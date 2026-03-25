"""
AegisForge Whale Tracker
=========================
Monitors large token transfers ("whale movements") across EVM chains.
Ported from local-whale-wallet (Node.js) into AegisForge's Python engine.

Features:
- Multi-chain support (Ethereum, Base, BSC)
- Real-time Transfer event listening via websocket/polling
- Coordinated movement detection (multiple large TXs in short window)
- Signal generation for the trading engine
- SQLite-based local storage (no Postgres dependency)

Usage:
    from engine.core.whale_tracker import WhaleTracker
    tracker = WhaleTracker()
    await tracker.start()
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("AegisEngine.WhaleTracker")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "whale_tracker.db"

# Minimum USD value to qualify as a "whale" transfer
WHALE_THRESHOLD_USD = 50_000
# Window for coordinated movement detection
COORDINATION_WINDOW_MINUTES = 10
# Min transfers in window to trigger alert
COORDINATION_MIN_COUNT = 3


@dataclass
class WhaleTransfer:
    tx_hash: str
    chain: str
    token_symbol: str
    token_address: str
    from_address: str
    to_address: str
    amount: float
    amount_usd: float
    timestamp: float
    from_label: Optional[str] = None
    to_label: Optional[str] = None


@dataclass
class WhaleSignal:
    signal_type: str  # "coordinated", "large_single", "accumulation", "distribution"
    description: str
    address: str
    chain: str
    transfer_count: int = 0
    total_usd: float = 0.0
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    payload: dict = field(default_factory=dict)


class WhaleTrackerDB:
    """SQLite storage for whale tracker data."""

    def __init__(self, db_path: Path = DB_PATH):
        DATA_DIR.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS whales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                label TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT NOT NULL,
                chain TEXT NOT NULL,
                token_symbol TEXT,
                token_address TEXT NOT NULL,
                from_address TEXT NOT NULL,
                to_address TEXT NOT NULL,
                amount REAL NOT NULL,
                amount_usd REAL,
                timestamp REAL NOT NULL,
                from_label TEXT,
                to_label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_type TEXT NOT NULL,
                description TEXT NOT NULL,
                address TEXT,
                chain TEXT,
                transfer_count INTEGER DEFAULT 0,
                total_usd REAL DEFAULT 0,
                payload TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_transfers_from ON transfers(from_address);
            CREATE INDEX IF NOT EXISTS idx_transfers_to ON transfers(to_address);
            CREATE INDEX IF NOT EXISTS idx_transfers_timestamp ON transfers(timestamp);
            CREATE INDEX IF NOT EXISTS idx_transfers_chain ON transfers(chain);
            CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(signal_type);
        """)
        self.conn.commit()

    def insert_transfer(self, t: WhaleTransfer):
        self.conn.execute(
            """INSERT INTO transfers
               (tx_hash, chain, token_symbol, token_address, from_address, to_address,
                amount, amount_usd, timestamp, from_label, to_label)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (t.tx_hash, t.chain, t.token_symbol, t.token_address,
             t.from_address, t.to_address, t.amount, t.amount_usd,
             t.timestamp, t.from_label, t.to_label)
        )
        self.conn.commit()

    def insert_signal(self, s: WhaleSignal):
        self.conn.execute(
            """INSERT INTO signals
               (signal_type, description, address, chain, transfer_count, total_usd, payload, detected_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (s.signal_type, s.description, s.address, s.chain,
             s.transfer_count, s.total_usd, json.dumps(s.payload), s.detected_at)
        )
        self.conn.commit()

    def get_whale_label(self, address: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT label FROM whales WHERE address = ?", (address.lower(),)
        ).fetchone()
        return row["label"] if row else None

    def add_whale(self, address: str, label: str):
        self.conn.execute(
            "INSERT OR IGNORE INTO whales (address, label) VALUES (?, ?)",
            (address.lower(), label)
        )
        self.conn.commit()

    def get_recent_transfers(self, address: str, window_minutes: int = 10, min_usd: float = 50000) -> list[dict]:
        cutoff = time.time() - (window_minutes * 60)
        rows = self.conn.execute(
            """SELECT * FROM transfers
               WHERE (from_address = ? OR to_address = ?)
               AND amount_usd >= ? AND timestamp >= ?""",
            (address.lower(), address.lower(), min_usd, cutoff)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_signals(self, limit: int = 50) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM signals ORDER BY detected_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_top_whales(self, limit: int = 20) -> list[dict]:
        rows = self.conn.execute(
            """SELECT from_address as address, SUM(amount_usd) as total_usd, COUNT(*) as tx_count
               FROM transfers GROUP BY from_address
               ORDER BY total_usd DESC LIMIT ?""", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


class WhaleTracker:
    """
    Main whale tracking engine. Monitors EVM chains for large transfers
    and generates signals for the trading engine.
    """

    # Chain configs — will be populated from env/config
    CHAINS = {
        "ethereum": {
            "name": "Ethereum",
            "chain_id": 1,
            "tokens": [
                {"symbol": "USDC", "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "decimals": 6},
                {"symbol": "USDT", "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "decimals": 6},
            ]
        },
        "base": {
            "name": "Base",
            "chain_id": 8453,
            "tokens": [
                {"symbol": "USDC", "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "decimals": 6},
            ]
        },
        "bsc": {
            "name": "BSC",
            "chain_id": 56,
            "tokens": [
                {"symbol": "USDT", "address": "0x55d398326f99059fF775485246999027B3197955", "decimals": 18},
            ]
        },
    }

    # Stablecoin prices (hardcoded — they're stable)
    STABLE_PRICES = {"USDC": 1.0, "USDT": 1.0, "DAI": 1.0}

    def __init__(self):
        self.db = WhaleTrackerDB()
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        """Start monitoring all configured chains."""
        if self._running:
            return
        self._running = True
        logger.info("Whale tracker starting...")

        for chain_key, chain_cfg in self.CHAINS.items():
            rpc_url = self._get_rpc(chain_key)
            if not rpc_url:
                logger.warning(f"No RPC configured for {chain_cfg['name']}, skipping")
                continue
            task = asyncio.create_task(self._monitor_chain(chain_key, chain_cfg, rpc_url))
            self._tasks.append(task)

        logger.info(f"Whale tracker monitoring {len(self._tasks)} chains")

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("Whale tracker stopped")

    def _get_rpc(self, chain_key: str) -> Optional[str]:
        env_map = {
            "ethereum": "ETH_RPC_URL",
            "base": "BASE_RPC_URL",
            "bsc": "BSC_RPC_URL",
        }
        return os.environ.get(env_map.get(chain_key, ""))

    async def _monitor_chain(self, chain_key: str, chain_cfg: dict, rpc_url: str):
        """Poll for new Transfer events on a chain. Uses eth_getLogs polling."""
        try:
            # Dynamic import — only needed if actually monitoring
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                logger.error(f"Cannot connect to {chain_cfg['name']} RPC")
                return

            # ERC-20 Transfer event signature
            transfer_topic = w3.keccak(text="Transfer(address,address,uint256)").hex()

            last_block = w3.eth.block_number
            logger.info(f"Monitoring {chain_cfg['name']} from block {last_block}")

            while self._running:
                try:
                    current_block = w3.eth.block_number
                    if current_block <= last_block:
                        await asyncio.sleep(12)  # ~1 block time
                        continue

                    for token in chain_cfg["tokens"]:
                        logs = w3.eth.get_logs({
                            "fromBlock": last_block + 1,
                            "toBlock": current_block,
                            "address": Web3.to_checksum_address(token["address"]),
                            "topics": [transfer_topic],
                        })

                        for log_entry in logs:
                            await self._process_transfer(
                                w3, chain_key, chain_cfg["name"],
                                token, log_entry
                            )

                    last_block = current_block
                    await asyncio.sleep(12)

                except Exception as e:
                    logger.error(f"Error monitoring {chain_cfg['name']}: {e}")
                    await asyncio.sleep(30)

        except ImportError:
            logger.warning("web3 not installed — whale tracker running in passive mode (API-only)")
        except Exception as e:
            logger.error(f"Fatal error on {chain_cfg['name']}: {e}")

    async def _process_transfer(self, w3, chain_key: str, chain_name: str, token: dict, log_entry):
        """Process a single Transfer event log."""
        try:
            from_addr = "0x" + log_entry["topics"][1].hex()[-40:]
            to_addr = "0x" + log_entry["topics"][2].hex()[-40:]
            raw_value = int(log_entry["data"].hex(), 16)
            amount = raw_value / (10 ** token["decimals"])

            usd_price = self.STABLE_PRICES.get(token["symbol"], 0)
            amount_usd = amount * usd_price

            if amount_usd < WHALE_THRESHOLD_USD:
                return

            from_label = self.db.get_whale_label(from_addr)
            to_label = self.db.get_whale_label(to_addr)

            transfer = WhaleTransfer(
                tx_hash=log_entry["transactionHash"].hex(),
                chain=chain_name,
                token_symbol=token["symbol"],
                token_address=token["address"],
                from_address=from_addr.lower(),
                to_address=to_addr.lower(),
                amount=amount,
                amount_usd=amount_usd,
                timestamp=time.time(),
                from_label=from_label,
                to_label=to_label,
            )

            self.db.insert_transfer(transfer)
            logger.info(
                f"[WHALE] {chain_name} {token['symbol']} "
                f"${amount_usd:,.0f} from {from_label or from_addr[:10]}... "
                f"to {to_label or to_addr[:10]}..."
            )

            await self._detect_coordinated(transfer)

        except Exception as e:
            logger.error(f"Error processing transfer: {e}")

    async def _detect_coordinated(self, transfer: WhaleTransfer):
        """Check for coordinated whale movements."""
        for address in (transfer.from_address, transfer.to_address):
            recent = self.db.get_recent_transfers(
                address,
                window_minutes=COORDINATION_WINDOW_MINUTES,
                min_usd=WHALE_THRESHOLD_USD,
            )

            if len(recent) >= COORDINATION_MIN_COUNT:
                total_usd = sum(r["amount_usd"] for r in recent)
                label = self.db.get_whale_label(address) or address[:16]

                signal = WhaleSignal(
                    signal_type="coordinated",
                    description=f"{len(recent)} large transfers in {COORDINATION_WINDOW_MINUTES}min involving {label}",
                    address=address,
                    chain=transfer.chain,
                    transfer_count=len(recent),
                    total_usd=total_usd,
                    payload={
                        "window_minutes": COORDINATION_WINDOW_MINUTES,
                        "threshold_usd": WHALE_THRESHOLD_USD,
                        "tx_hashes": [r["tx_hash"] for r in recent[:10]],
                    },
                )

                self.db.insert_signal(signal)
                logger.warning(f"[ALERT] Coordinated whale movement: {signal.description}")

    # --- API Methods (for FastAPI integration) ---

    def get_recent_signals(self, limit: int = 50) -> list[dict]:
        return self.db.get_signals(limit)

    def get_top_movers(self, limit: int = 20) -> list[dict]:
        return self.db.get_top_whales(limit)

    def add_watched_whale(self, address: str, label: str):
        self.db.add_whale(address, label)

    def get_transfers_for_address(self, address: str, limit: int = 50) -> list[dict]:
        rows = self.db.conn.execute(
            """SELECT * FROM transfers
               WHERE from_address = ? OR to_address = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (address.lower(), address.lower(), limit)
        ).fetchall()
        return [dict(r) for r in rows]
