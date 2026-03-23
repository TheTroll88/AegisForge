"""
Standalone Aerodrome airdrop/points farmer for daily tiny swaps.

Required modular functions implemented:
- balance_check()
- approve()
- swap()
- send()

Default behavior:
- DRY_RUN=true (safe preview mode)
- RPC_URL=http://127.0.0.1:8545 (Anvil)

Live/testnet flip guidance:
- Set DRY_RUN=false
- Set RPC_URL to Base Sepolia: https://sepolia.base.org
- Set PRIVATE_KEY to the funded wallet key
- Keep DEDICATED_WALLET as the receiver

Required env vars (all must be set for live mode):
    PRIVATE_KEY           - Wallet private key (hex, with or without 0x prefix)
    DEDICATED_WALLET      - Receiver address for swapped tokens
    ROUTER_ADDRESS        - DEX router contract address
    USDC_ADDRESS          - USDC token contract on target chain
    TARGET_TOKEN_ADDRESS  - Token to swap into

Optional env vars:
    RPC_URL          - Chain RPC (default: Anvil localhost)
    DRY_RUN          - "true" to simulate only (default: true)
    GAS_PRICE_GWEI   - Manual gas price; omit for auto
    ROUTE_STABLE     - "true" if stable pair (default: false)
    ROUTE_FACTORY    - Factory address override

Troubleshooting:
    "Connection refused" on startup
        → Anvil isn't running. Start it with `anvil` or change RPC_URL to a real endpoint.

    Transaction reverts silently after ~20 minutes
        → The master deadline is 1200 seconds. If you're debugging and pausing,
          the tx expires. Restart the script for a fresh deadline.

    Swap fails with slippage error
        → Default slippage is 1%. For volatile tokens, set a wider tolerance
          in the Config dataclass or adjust min_amount_out logic.

    "Approval" transaction sent every time
        → First run approves max uint256 for the router. After that, approvals
          are skipped. If you change ROUTER_ADDRESS, a new approval is needed.
"""

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3


# -----------------------------
# Minimal ABIs required by bot
# -----------------------------
# ERC20 ABI with only the functions needed for this flow.
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

# Aerodrome Router swap signature using Route structs.
# Route tuple: (from, to, stable, factory)
ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {
                "components": [
                    {"internalType": "address", "name": "from", "type": "address"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "bool", "name": "stable", "type": "bool"},
                    {"internalType": "address", "name": "factory", "type": "address"},
                ],
                "internalType": "struct Route[]",
                "name": "routes",
                "type": "tuple[]",
            },
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


@dataclass
class Config:
    """Runtime settings loaded from environment variables."""

    rpc_url: str
    private_key: str
    dedicated_wallet: str
    router_address: str
    usdc_address: str
    target_token_address: str
    target_token_symbol: str
    route_stable: bool
    route_factory: str
    min_usdc_balance: Decimal
    swap_amount_usdc: Decimal
    slippage_bps: int
    deadline_seconds: int
    loop_seconds: int
    max_retries: int
    retry_delay_seconds: int
    dry_run: bool
    gas_price_gwei: Optional[Decimal]


def _as_bool(value: str, default: bool = False) -> bool:
    """Parse booleans from env text safely."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> Config:
    """Load and validate all config from .env / environment."""
    load_dotenv()

    rpc_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv("PRIVATE_KEY", "").strip()
    dedicated_wallet = os.getenv("DEDICATED_WALLET", "").strip()
    router_address = os.getenv("ROUTER_ADDRESS", "").strip()
    usdc_address = os.getenv("USDC_ADDRESS", "").strip()
    target_token_address = os.getenv("TARGET_TOKEN_ADDRESS", "").strip()
    target_token_symbol = os.getenv("TARGET_TOKEN_SYMBOL", "TOKEN").strip()

    if not private_key:
        raise ValueError("Missing PRIVATE_KEY in environment.")
    if not dedicated_wallet:
        raise ValueError("Missing DEDICATED_WALLET in environment.")
    if not router_address:
        raise ValueError("Missing ROUTER_ADDRESS in environment.")
    if not usdc_address:
        raise ValueError("Missing USDC_ADDRESS in environment.")
    if not target_token_address:
        raise ValueError("Missing TARGET_TOKEN_ADDRESS in environment.")

    route_stable = _as_bool(os.getenv("ROUTE_STABLE", "false"), default=False)
    route_factory = os.getenv("ROUTE_FACTORY", "0x0000000000000000000000000000000000000000").strip()

    min_usdc_balance = Decimal(os.getenv("MIN_USDC_BALANCE", "0.001"))
    swap_amount_usdc = Decimal(os.getenv("SWAP_AMOUNT_USDC", "0.01"))
    slippage_bps = int(os.getenv("SLIPPAGE_BPS", "100"))
    deadline_seconds = int(os.getenv("DEADLINE_SECONDS", "1200"))
    loop_seconds = int(os.getenv("LOOP_SECONDS", "86400"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay_seconds = int(os.getenv("RETRY_DELAY_SECONDS", "15"))
    dry_run = _as_bool(os.getenv("DRY_RUN", "true"), default=True)

    gas_price_raw = os.getenv("GAS_PRICE_GWEI", "").strip()
    gas_price_gwei = Decimal(gas_price_raw) if gas_price_raw else None

    return Config(
        rpc_url=rpc_url,
        private_key=private_key,
        dedicated_wallet=dedicated_wallet,
        router_address=router_address,
        usdc_address=usdc_address,
        target_token_address=target_token_address,
        target_token_symbol=target_token_symbol,
        route_stable=route_stable,
        route_factory=route_factory,
        min_usdc_balance=min_usdc_balance,
        swap_amount_usdc=swap_amount_usdc,
        slippage_bps=slippage_bps,
        deadline_seconds=deadline_seconds,
        loop_seconds=loop_seconds,
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
        dry_run=dry_run,
        gas_price_gwei=gas_price_gwei,
    )


def _logs_dir() -> Path:
    """Create a local logs directory for this module only."""
    here = Path(__file__).resolve().parent
    out = here / "logs"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _ts() -> str:
    """UTC timestamp helper for readable logs."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(event: str, payload: Dict[str, Any]) -> None:
    """Append JSONL log records for traceability and tx auditing."""
    entry = {"timestamp_utc": _ts(), "event": event, **payload}
    print(json.dumps(entry, ensure_ascii=True))

    log_file = _logs_dir() / "farmer_log.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=True) + "\n")


def _to_checksum(w3: Web3, addr: str) -> str:
    """Normalize addresses to checksum format."""
    return w3.to_checksum_address(addr)


def _contract_exists(w3: Web3, address: str) -> bool:
    """Check if there is bytecode at address (useful for Anvil dry-runs)."""
    code = w3.eth.get_code(address)
    return code not in (b"", b"0x", "0x")


def _build_and_send_tx(
    w3: Web3,
    account: Account,
    tx: Dict[str, Any],
    *,
    dry_run: bool,
) -> Optional[str]:
    """
    Build/sign/send a transaction.

    Returns tx hash hex when sent, None when dry-run only.
    """
    if dry_run:
        log_event("dry_run_tx", {"tx_preview": tx})
        return None

    signed = w3.eth.account.sign_transaction(tx, private_key=account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hash_hex = w3.to_hex(tx_hash)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    log_event(
        "tx_confirmed",
        {
            "tx_hash": tx_hash_hex,
            "status": receipt.status,
            "gas_used": receipt.gasUsed,
            "block_number": receipt.blockNumber,
        },
    )
    return tx_hash_hex


def _base_tx_fields(w3: Web3, from_addr: str, gas_price_gwei: Optional[Decimal]) -> Dict[str, Any]:
    """Generate nonce + gas fields for a standard EVM tx."""
    tx: Dict[str, Any] = {
        "from": from_addr,
        "nonce": w3.eth.get_transaction_count(from_addr),
        "chainId": w3.eth.chain_id,
    }

    if gas_price_gwei is not None:
        tx["gasPrice"] = w3.to_wei(float(gas_price_gwei), "gwei")

    return tx


def balance_check(
    w3: Web3,
    usdc,
    owner: str,
    min_required_human: Decimal,
) -> Tuple[bool, int, int]:
    """
    Check current USDC balance and validate it is above configured threshold.

    Returns:
    - allowed_to_trade: bool
    - raw_balance: int
    - usdc_decimals: int
    """
    decimals = usdc.functions.decimals().call()
    raw_balance = usdc.functions.balanceOf(owner).call()

    human_balance = Decimal(raw_balance) / (Decimal(10) ** decimals)
    allowed = human_balance > min_required_human

    log_event(
        "balance_check",
        {
            "owner": owner,
            "raw_balance": str(raw_balance),
            "human_balance": str(human_balance),
            "min_required": str(min_required_human),
            "allowed": allowed,
        },
    )

    return allowed, raw_balance, decimals


def approve(
    w3: Web3,
    cfg: Config,
    account: Account,
    usdc,
    owner: str,
    spender: str,
    min_allowance_needed: int,
) -> Optional[str]:
    """
    Approve router once if allowance is too low.

    Uses max uint256 so repeated daily swaps do not need re-approval.
    """
    current_allowance = usdc.functions.allowance(owner, spender).call()
    if current_allowance >= min_allowance_needed:
        log_event(
            "approve_skip",
            {
                "reason": "allowance_sufficient",
                "current_allowance": str(current_allowance),
                "required": str(min_allowance_needed),
            },
        )
        return None

    max_uint = (1 << 256) - 1

    tx = usdc.functions.approve(spender, max_uint).build_transaction(
        {
            **_base_tx_fields(w3, owner, cfg.gas_price_gwei),
            "gas": 120000,
        }
    )

    log_event(
        "approve_submit",
        {
            "owner": owner,
            "spender": spender,
            "amount": str(max_uint),
        },
    )

    return _build_and_send_tx(w3, account, tx, dry_run=cfg.dry_run)


def swap(
    w3: Web3,
    cfg: Config,
    account: Account,
    router,
    owner: str,
    amount_in: int,
) -> Optional[str]:
    """
    Swap USDC -> target token on Aerodrome using a single route.

    amountOutMin is computed from slippage setting as a conservative floor:
    for dry-run simplicity, we apply a basis-point haircut to amountIn units.
    """
    deadline = int(time.time()) + cfg.deadline_seconds

    # In production you would quote expected output and derive minOut from quote.
    # For a generic modular bot, we use a protective minimum based on configured slippage.
    amount_out_min = int(amount_in * (10_000 - cfg.slippage_bps) / 10_000)

    route = [
        (
            _to_checksum(w3, cfg.usdc_address),
            _to_checksum(w3, cfg.target_token_address),
            cfg.route_stable,
            _to_checksum(w3, cfg.route_factory),
        )
    ]

    tx = router.functions.swapExactTokensForTokens(
        amount_in,
        amount_out_min,
        route,
        owner,
        deadline,
    ).build_transaction(
        {
            **_base_tx_fields(w3, owner, cfg.gas_price_gwei),
            "gas": 550000,
        }
    )

    log_event(
        "swap_submit",
        {
            "amount_in": str(amount_in),
            "amount_out_min": str(amount_out_min),
            "route": [
                {
                    "from": route[0][0],
                    "to": route[0][1],
                    "stable": route[0][2],
                    "factory": route[0][3],
                }
            ],
            "deadline": deadline,
            "target_symbol": cfg.target_token_symbol,
        },
    )

    return _build_and_send_tx(w3, account, tx, dry_run=cfg.dry_run)


def send(
    w3: Web3,
    cfg: Config,
    account: Account,
    token,
    from_addr: str,
    to_addr: str,
) -> Optional[str]:
    """
    Forward all received target tokens to the dedicated wallet.

    If target balance is zero, skip cleanly.
    """
    token_balance = token.functions.balanceOf(from_addr).call()
    if token_balance <= 0:
        log_event("send_skip", {"reason": "no_target_token_balance", "from": from_addr})
        return None

    tx = token.functions.transfer(to_addr, token_balance).build_transaction(
        {
            **_base_tx_fields(w3, from_addr, cfg.gas_price_gwei),
            "gas": 150000,
        }
    )

    log_event(
        "send_submit",
        {
            "from": from_addr,
            "to": to_addr,
            "amount": str(token_balance),
            "symbol": cfg.target_token_symbol,
        },
    )

    return _build_and_send_tx(w3, account, tx, dry_run=cfg.dry_run)


def run_cycle(cfg: Config) -> None:
    """Run one full farmer cycle with validation + swap + forwarding."""
    w3 = Web3(Web3.HTTPProvider(cfg.rpc_url, request_kwargs={"timeout": 60}))
    if not w3.is_connected():
        raise RuntimeError(f"RPC not reachable: {cfg.rpc_url}")

    acct = w3.eth.account.from_key(cfg.private_key)
    owner = _to_checksum(w3, acct.address)

    router_addr = _to_checksum(w3, cfg.router_address)
    usdc_addr = _to_checksum(w3, cfg.usdc_address)
    target_addr = _to_checksum(w3, cfg.target_token_address)
    dedicated_addr = _to_checksum(w3, cfg.dedicated_wallet)

    # Safety check: in non-dry mode, ensure contracts exist at configured addresses.
    if not cfg.dry_run:
        if not _contract_exists(w3, router_addr):
            raise RuntimeError(f"Router contract not found at {router_addr}")
        if not _contract_exists(w3, usdc_addr):
            raise RuntimeError(f"USDC contract not found at {usdc_addr}")
        if not _contract_exists(w3, target_addr):
            raise RuntimeError(f"Target token contract not found at {target_addr}")

    usdc = w3.eth.contract(address=usdc_addr, abi=ERC20_ABI)
    target = w3.eth.contract(address=target_addr, abi=ERC20_ABI)
    router = w3.eth.contract(address=router_addr, abi=ROUTER_ABI)

    # 1) Check USDC balance threshold.
    can_trade, raw_usdc, usdc_decimals = balance_check(w3, usdc, owner, cfg.min_usdc_balance)
    if not can_trade:
        log_event(
            "cycle_skip",
            {
                "reason": "insufficient_usdc",
                "raw_usdc": str(raw_usdc),
                "min_required": str(cfg.min_usdc_balance),
            },
        )
        return

    # Convert configured human USDC amount into token units.
    desired_amount_in = int(cfg.swap_amount_usdc * (Decimal(10) ** usdc_decimals))
    if desired_amount_in <= 0:
        raise ValueError("SWAP_AMOUNT_USDC is too small after decimal conversion.")

    # Cap to available balance so we never over-request a swap.
    amount_in = min(desired_amount_in, raw_usdc)

    # 2) Approve router once (or skip if already approved).
    approve(w3, cfg, acct, usdc, owner, router_addr, amount_in)

    # 3) Perform tiny daily swap.
    swap(w3, cfg, acct, router, owner, amount_in)

    # 4) Forward resulting token balance to dedicated wallet.
    send(w3, cfg, acct, target, owner, dedicated_addr)


def main() -> None:
    """Daily loop with retry policy and clear console/log status output."""
    cfg = load_config()

    log_event(
        "startup",
        {
            "rpc_url": cfg.rpc_url,
            "dry_run": cfg.dry_run,
            "loop_seconds": cfg.loop_seconds,
            "max_retries": cfg.max_retries,
            "target_symbol": cfg.target_token_symbol,
            "note_live_flip": "Set DRY_RUN=false + update RPC_URL/PRIVATE_KEY for live.",
        },
    )

    while True:
        # Retries are per cycle to make transient RPC/network/router failures non-fatal.
        success = False
        for attempt in range(1, cfg.max_retries + 1):
            try:
                log_event("cycle_start", {"attempt": attempt})
                run_cycle(cfg)
                log_event("cycle_done", {"attempt": attempt, "success": True})
                success = True
                break
            except Exception as exc:  # noqa: BLE001
                log_event(
                    "cycle_error",
                    {
                        "attempt": attempt,
                        "error": str(exc),
                    },
                )
                if attempt < cfg.max_retries:
                    time.sleep(cfg.retry_delay_seconds)

        if not success:
            log_event("cycle_failed", {"all_retries_exhausted": True})

        # Required by request: sleep for one day between runs.
        log_event("sleep", {"seconds": cfg.loop_seconds})
        time.sleep(cfg.loop_seconds)


if __name__ == "__main__":
    main()
