# engine/core/wallet_manager.py

import logging
import os
import json
import pathlib
from datetime import datetime
from typing import Optional
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import time
from core.decimals_cache import DecimalsCache

# Load project root .env first, then allow local overrides.
_project_root = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(_project_root / ".env")
load_dotenv()

class WalletManager:
    """Manages MetaMask wallet connection and transactions"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.decimals_cache = DecimalsCache(logger=self.logger)
        
        # Network Configuration
        self.rpc_url = os.getenv("METAMASK_RPC_URL", "https://polygon-rpc.com")
        self.chain_id = int(os.getenv("METAMASK_CHAIN_ID", 137))  # Polygon mainnet
        self.private_key = os.getenv("METAMASK_PRIVATE_KEY")
        self.wallet_address = os.getenv("METAMASK_WALLET_ADDRESS")
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"❌ Failed to connect to {self.rpc_url}")

        actual_chain_id = int(self.w3.eth.chain_id)
        if actual_chain_id != self.chain_id:
            raise ConnectionError(f"❌ RPC chain ID mismatch: expected {self.chain_id}, got {actual_chain_id}")

        self.logger.info(f"✅ Connected to chain ID: {self.chain_id}")

        # Tx receipt logging (optional but enabled by default)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        default_receipt_log = os.path.join(project_root, "kratos_core", "logs", "tx_receipts.json")
        self.tx_receipt_log = os.getenv("TX_RECEIPT_LOG_FILE", default_receipt_log)
        try:
            os.makedirs(os.path.dirname(self.tx_receipt_log), exist_ok=True)
            if not os.path.exists(self.tx_receipt_log):
                with open(self.tx_receipt_log, "w") as f:
                    json.dump([], f)
        except Exception as e:
            self.logger.warning(f"⚠️ Unable to initialize tx receipt log: {e}")
        
        # Account setup
        if self.private_key:
            try:
                self.account = Account.from_key(self.private_key)
                self.wallet_address = self.account.address
                self.logger.info(f"✅ Loaded account: {self.wallet_address}")
            except Exception as e:
                self.logger.error(f"❌ Invalid private key: {e}")
                self.account = None
        else:
            self.logger.warning("⚠️ No private key found. Read-only mode only.")
            self.account = None

    def get_balance(self, token_address: Optional[str] = None) -> float:
        """Get ETH/MATIC balance or ERC20 token balance"""
        try:
            if token_address is None:
                # Get native ETH/MATIC balance
                balance_wei = self._retry_rpc(self.w3.eth.get_balance, self.wallet_address)
                balance = self.w3.from_wei(balance_wei, "ether")
                self.logger.info(f"💰 Native Balance: {balance:.6f}")
                return balance
            else:
                # Get ERC20 token balance
                from core.dex_trader import ERC20_ABI
                try:
                    addr = Web3.to_checksum_address(token_address)
                except Exception:
                    addr = token_address
                contract = self.w3.eth.contract(address=addr, abi=ERC20_ABI)
                balance = self._retry_rpc(contract.functions.balanceOf(self.wallet_address).call)
                decimals = self.decimals_cache.get(addr)
                if decimals is None:
                    try:
                        decimals = self._retry_rpc(contract.functions.decimals().call)
                        self.decimals_cache.set(addr, decimals)
                    except Exception:
                        decimals = 18
                balance_readable = balance / (10 ** decimals)
                self.logger.info(f"💰 Token Balance: {balance_readable:.6f}")
                return balance_readable
        except Exception as e:
            self.logger.error(f"❌ Failed to get balance: {e}")
            return 0.0

    def get_gas_price(self) -> float:
        """Get current gas price in GWEI"""
        try:
            gas_price = self._retry_rpc(lambda: self.w3.eth.gas_price)
            gas_price_gwei = self.w3.from_wei(gas_price, "gwei")
            self.logger.info(f"⛽ Gas Price: {gas_price_gwei:.2f} GWEI")
            return float(gas_price_gwei)
        except Exception as e:
            self.logger.error(f"❌ Failed to get gas price: {e}")
            return 0.0

    def estimate_transaction_cost(self, gas_used: int) -> float:
        """Estimate transaction cost in MATIC"""
        try:
            gas_price = self._retry_rpc(lambda: self.w3.eth.gas_price)
            cost_wei = gas_used * gas_price
            cost_matic = self.w3.from_wei(cost_wei, "ether")
            self.logger.info(f"💸 Est. TX Cost: {cost_matic:.6f} MATIC")
            return float(cost_matic)
        except Exception as e:
            self.logger.error(f"❌ Failed to estimate cost: {e}")
            return 0.0

    def send_transaction(self, tx_dict: dict) -> Optional[str]:
        """Sign and send a transaction, return tx hash"""
        if not self.account:
            self.logger.error("❌ No account available for signing")
            return None
        
        try:
            # Fill in account address
            tx_dict["from"] = self.account.address
            
            # Get nonce (pending to avoid collisions)
            tx_dict["nonce"] = self._retry_rpc(self.w3.eth.get_transaction_count, self.account.address, "pending")
            
            # Set chain ID
            tx_dict["chainId"] = self.chain_id
            
            # Estimate gas if not provided
            if "gas" not in tx_dict:
                tx_dict["gas"] = self._retry_rpc(self.w3.eth.estimate_gas, tx_dict)
            
            # Get gas price
            if "gasPrice" not in tx_dict:
                tx_dict["gasPrice"] = self._retry_rpc(lambda: self.w3.eth.gas_price)
            
            self.logger.info(f"📝 Signing transaction: {tx_dict}")
            
            # Sign transaction
            signed_tx = self.account.sign_transaction(tx_dict)

            # Support different attribute names across eth-account/web3 versions
            raw_tx = None
            if hasattr(signed_tx, 'rawTransaction'):
                raw_tx = getattr(signed_tx, 'rawTransaction')
            elif hasattr(signed_tx, 'raw_transaction'):
                raw_tx = getattr(signed_tx, 'raw_transaction')
            elif isinstance(signed_tx, dict):
                raw_tx = signed_tx.get('rawTransaction') or signed_tx.get('raw_transaction')

            if raw_tx is None:
                self.logger.error('❌ Unable to locate raw signed transaction bytes')
                return None

            # Send transaction
            try:
                tx_hash = self._retry_rpc(self.w3.eth.send_raw_transaction, raw_tx)
            except Exception as e:
                if "nonce too low" in str(e).lower():
                    tx_dict["nonce"] = self._retry_rpc(self.w3.eth.get_transaction_count, self.account.address, "pending")
                    signed_tx = self.account.sign_transaction(tx_dict)
                    raw_tx = getattr(signed_tx, 'rawTransaction', None) or getattr(signed_tx, 'raw_transaction', None)
                    if raw_tx is None and isinstance(signed_tx, dict):
                        raw_tx = signed_tx.get('rawTransaction') or signed_tx.get('raw_transaction')
                    if raw_tx is None:
                        raise
                    tx_hash = self._retry_rpc(self.w3.eth.send_raw_transaction, raw_tx)
                else:
                    raise
            try:
                tx_hash_hex = tx_hash.hex()
            except Exception:
                from web3 import Web3
                tx_hash_hex = Web3.toHex(tx_hash)
            
            self.logger.info(f"✅ TX Sent: {tx_hash_hex}")
            return tx_hash_hex
        except Exception as e:
            self.logger.error(f"❌ Failed to send transaction: {e}")
            return None

    def wait_for_receipt(self, tx_hash: str, timeout: int = 300) -> Optional[dict]:
        """Wait for transaction confirmation"""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            if receipt.get('status') != 1:
                self.logger.error(f"❌ TX Reverted: {receipt['transactionHash'].hex()}")
                self._log_tx_receipt(tx_hash, receipt=receipt, status="reverted")
                return None
            self.logger.info(f"✅ TX Confirmed: {receipt['transactionHash'].hex()}")
            self._log_tx_receipt(tx_hash, receipt=receipt, status="confirmed")
            return receipt
        except Exception as e:
            self.logger.error(f"❌ Transaction failed or timeout: {e}")
            self._log_tx_receipt(tx_hash, receipt=None, status="error", error=str(e))
            return None

    def pending_tx_count(self) -> int:
        """Return number of pending transactions for the account."""
        try:
            latest = self._retry_rpc(self.w3.eth.get_transaction_count, self.account.address, "latest")
            pending = self._retry_rpc(self.w3.eth.get_transaction_count, self.account.address, "pending")
            return max(0, pending - latest)
        except Exception:
            return 0

    def _retry_rpc(self, fn, *args, retries: int = 5, backoff: float = 0.5, **kwargs):
        """Retry wrapper for RPC calls to handle rate limits (429) and transient errors."""
        last_exc = None
        for i in range(retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
                msg = str(e)
                if '429' in msg or 'Too Many Requests' in msg or 'rate limit' in msg.lower():
                    sleep_time = backoff * (2 ** i)
                    self.logger.warning(f"⚠️ RPC rate limited, retrying in {sleep_time:.1f}s ({i+1}/{retries})")
                    time.sleep(sleep_time)
                    continue
                # For other transient network errors, also retry a few times
                if 'timed out' in msg.lower() or 'connection' in msg.lower():
                    sleep_time = backoff * (2 ** i)
                    self.logger.warning(f"⚠️ RPC transient error, retrying in {sleep_time:.1f}s ({i+1}/{retries})")
                    time.sleep(sleep_time)
                    continue
                raise
        # If here, raise the last exception
        raise last_exc

    def _log_tx_receipt(self, tx_hash: str, receipt: Optional[dict], status: str, error: Optional[str] = None) -> None:
        """Append a tx receipt status record for troubleshooting."""
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "tx_hash": tx_hash,
                "status": status,
            }
            if receipt:
                record.update({
                    "block_number": receipt.get("blockNumber"),
                    "gas_used": receipt.get("gasUsed"),
                    "effective_gas_price": receipt.get("effectiveGasPrice"),
                    "receipt_status": receipt.get("status"),
                })
                txh = receipt.get("transactionHash")
                if txh is not None:
                    try:
                        record["tx_hash"] = txh.hex()
                    except Exception:
                        pass
            if error:
                record["error"] = error

            if not self.tx_receipt_log:
                return

            with open(self.tx_receipt_log, "r+") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []
                if not isinstance(data, list):
                    data = []
                data.append(record)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to log tx receipt: {e}")
