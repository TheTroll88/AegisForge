# engine/core/asig_bridge.py
"""
ASIGBridge — connects AegisForge to the deployed ASIG token and SignalRegistry
contracts on Base mainnet. Read-only by default; write ops require PRIVATE_KEY.
"""

import logging
import os
from typing import List, Optional

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# --- Contract addresses (Base mainnet) ---
ASIG_TOKEN_ADDRESS = "0x30610a21764bb38c43a2e532cfba91c9db927994"
SIGNAL_REGISTRY_ADDRESS = "0xb5AFac365FD2968157EFF7183144e46F11772926"
BASE_CHAIN_ID = 8453
DEFAULT_BASE_RPC = "https://mainnet.base.org"

# --- Minimal ABIs (only the functions/events we use) ---
ASIG_TOKEN_ABI = [
    {"constant": True, "inputs": [{"name": "account", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}],
     "type": "function", "stateMutability": "view"},
    {"constant": True, "inputs": [],
     "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}],
     "type": "function", "stateMutability": "view"},
    {"constant": True, "inputs": [],
     "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],
     "type": "function", "stateMutability": "view"},
    {"constant": False,
     "inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}],
     "name": "transfer", "outputs": [{"name": "", "type": "bool"}],
     "type": "function", "stateMutability": "nonpayable"},
    {"constant": False,
     "inputs": [{"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "", "type": "bool"}],
     "type": "function", "stateMutability": "nonpayable"},
    {"constant": False,
     "inputs": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"}],
     "name": "transferFrom", "outputs": [{"name": "", "type": "bool"}],
     "type": "function", "stateMutability": "nonpayable"},
    {"anonymous": False,
     "inputs": [{"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"}],
     "name": "Transfer", "type": "event"},
]

SIGNAL_REGISTRY_ABI = [
    {"inputs": [{"name": "_command", "type": "string"}],
     "name": "createSignal", "outputs": [],
     "type": "function", "stateMutability": "nonpayable"},
    {"inputs": [{"name": "", "type": "uint256"}],
     "name": "signals",
     "outputs": [{"name": "creator", "type": "address"},
                  {"name": "command", "type": "string"},
                  {"name": "timestamp", "type": "uint256"}],
     "type": "function", "stateMutability": "view"},
    {"anonymous": False,
     "inputs": [{"indexed": True, "name": "creator", "type": "address"},
                {"indexed": False, "name": "command", "type": "string"},
                {"indexed": False, "name": "timestamp", "type": "uint256"}],
     "name": "SignalCreated", "type": "event"},
]


class ASIGBridge:
    """Read/write bridge to ASIG token and SignalRegistry on Base."""

    def __init__(self, rpc_url: Optional[str] = None, private_key: Optional[str] = None):
        self.logger = logging.getLogger("asig_bridge")
        self.rpc_url = rpc_url or os.getenv("BASE_RPC_URL", DEFAULT_BASE_RPC)
        self.private_key = private_key or os.getenv("PRIVATE_KEY") or os.getenv("METAMASK_PRIVATE_KEY")
        self.wallet_address: Optional[str] = None

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            self.logger.warning("⚠️ ASIGBridge: cannot reach Base RPC — chain calls will fail")

        # Derive wallet from private key if available
        if self.private_key:
            try:
                from eth_account import Account
                acct = Account.from_key(self.private_key)
                self.wallet_address = acct.address
            except Exception as e:
                self.logger.warning(f"⚠️ ASIGBridge: bad private key — write ops disabled ({e})")
                self.private_key = None

        # Contract instances
        self.asig_token = self.w3.eth.contract(
            address=Web3.to_checksum_address(ASIG_TOKEN_ADDRESS),
            abi=ASIG_TOKEN_ABI,
        )
        self.signal_registry = self.w3.eth.contract(
            address=Web3.to_checksum_address(SIGNAL_REGISTRY_ADDRESS),
            abi=SIGNAL_REGISTRY_ABI,
        )

    # ------------------------------------------------------------------ reads

    def get_asig_balance(self, address: Optional[str] = None) -> Optional[float]:
        """Return ASIG balance (human-readable) for *address* or own wallet."""
        try:
            addr = Web3.to_checksum_address(address or self.wallet_address or "0x" + "0" * 40)
            raw = self.asig_token.functions.balanceOf(addr).call()
            decimals = self.asig_token.functions.decimals().call()
            return raw / (10 ** decimals)
        except Exception as e:
            self.logger.error(f"ASIGBridge.get_asig_balance failed: {e}")
            return None

    def get_total_supply(self) -> Optional[float]:
        """Return ASIG total supply (human-readable)."""
        try:
            raw = self.asig_token.functions.totalSupply().call()
            decimals = self.asig_token.functions.decimals().call()
            return raw / (10 ** decimals)
        except Exception as e:
            self.logger.error(f"ASIGBridge.get_total_supply failed: {e}")
            return None

    def get_recent_signals(self, count: int = 20) -> List[dict]:
        """Read the last *count* signals from SignalRegistry (on-chain array)."""
        results: List[dict] = []
        try:
            # The contract stores signals in a public array; there's no length
            # getter, so we probe from index 0 until we get a revert, then
            # return the tail.
            idx = 0
            all_signals: List[dict] = []
            while True:
                try:
                    creator, command, ts = self.signal_registry.functions.signals(idx).call()
                    all_signals.append({
                        "index": idx,
                        "creator": creator,
                        "command": command,
                        "timestamp": int(ts),
                    })
                    idx += 1
                except Exception:
                    break  # past end of array
            results = all_signals[-count:] if len(all_signals) > count else all_signals
        except Exception as e:
            self.logger.error(f"ASIGBridge.get_recent_signals failed: {e}")
        return results

    # ----------------------------------------------------------------- writes

    def _send_tx(self, tx_func):
        """Build, sign, and send a contract write call. Returns tx hash hex or None."""
        if not self.private_key or not self.wallet_address:
            self.logger.warning("ASIGBridge: no private key — skipping write op")
            return None
        try:
            addr = Web3.to_checksum_address(self.wallet_address)
            nonce = self.w3.eth.get_transaction_count(addr)
            tx = tx_func.build_transaction({
                "from": addr,
                "nonce": nonce,
                "gas": 200_000,
                "gasPrice": self.w3.eth.gas_price,
                "chainId": BASE_CHAIN_ID,
            })
            signed = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            hex_hash = tx_hash.hex()
            self.logger.info(f"ASIGBridge tx sent: {hex_hash}")
            return hex_hash
        except Exception as e:
            self.logger.error(f"ASIGBridge._send_tx failed: {e}")
            return None

    def broadcast_signal(self, command: str) -> Optional[str]:
        """Broadcast a trade signal to SignalRegistry on-chain.

        *command* format examples:
            "BUY:ETH/USD:RSI:0.85"
            "SELL:BTC/USD:FUSION:0.72"

        Returns tx hash hex string or None on failure / no key.
        """
        self.logger.info(f"ASIGBridge broadcasting signal: {command}")
        return self._send_tx(self.signal_registry.functions.createSignal(command))

    def transfer_asig(self, to_address: str, amount: float) -> Optional[str]:
        """Transfer *amount* ASIG tokens to *to_address*. Returns tx hash or None."""
        try:
            decimals = self.asig_token.functions.decimals().call()
            raw_amount = int(amount * (10 ** decimals))
            to = Web3.to_checksum_address(to_address)
            return self._send_tx(self.asig_token.functions.transfer(to, raw_amount))
        except Exception as e:
            self.logger.error(f"ASIGBridge.transfer_asig failed: {e}")
            return None
