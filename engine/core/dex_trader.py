# engine/core/dex_trader.py

import logging
import os
import time
from typing import Optional, Tuple
from web3 import Web3
from dotenv import load_dotenv
import requests
from core.decimals_cache import DecimalsCache

load_dotenv()

# Standard ERC20 ABI
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

# Uniswap V3 Router ABI (SwapRouter, includes deadline)
UNISWAP_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "params", "type": "tuple", "components": [
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"},
                {"name": "fee", "type": "uint24"},
                {"name": "recipient", "type": "address"},
                {"name": "deadline", "type": "uint256"},
                {"name": "amountIn", "type": "uint256"},
                {"name": "amountOutMinimum", "type": "uint256"},
                {"name": "sqrtPriceLimitX96", "type": "uint160"}
            ]}
        ],
        "name": "exactInputSingle",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "type": "function"
    }
]

# Uniswap V3 SwapRouter02 ABI (no deadline)
UNISWAP_ROUTER02_ABI = [
    {
        "inputs": [
            {"name": "params", "type": "tuple", "components": [
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"},
                {"name": "fee", "type": "uint24"},
                {"name": "recipient", "type": "address"},
                {"name": "amountIn", "type": "uint256"},
                {"name": "amountOutMinimum", "type": "uint256"},
                {"name": "sqrtPriceLimitX96", "type": "uint160"}
            ]}
        ],
        "name": "exactInputSingle",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "type": "function"
    }
]

# Uniswap V3 Factory ABI
UNISWAP_FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Uniswap V3 Pool ABI (minimal)
UNISWAP_POOL_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"name": "sqrtPriceX96", "type": "uint160"},
            {"name": "tick", "type": "int24"},
            {"name": "observationIndex", "type": "uint16"},
            {"name": "observationCardinality", "type": "uint16"},
            {"name": "observationCardinalityNext", "type": "uint16"},
            {"name": "feeProtocol", "type": "uint8"},
            {"name": "unlocked", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Uniswap V3 Quoter ABI (supports v1 and v2 signatures)
UNISWAP_QUOTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "sqrtPriceX96", "type": "uint160"},
            {"name": "initializedTicksCrossed", "type": "uint32"},
            {"name": "gasEstimate", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "tokenIn", "type": "address"},
            {"name": "tokenOut", "type": "address"},
            {"name": "fee", "type": "uint24"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "sqrtPriceLimitX96", "type": "uint160"}
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

class DEXTrader:
    """Trade on Uniswap V3 (Base mainnet)"""
    
    def __init__(self, wallet_manager, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.wallet = wallet_manager
        self.w3 = wallet_manager.w3
        self.decimals_cache = DecimalsCache(logger=self.logger)
        
        # Uniswap Router V3 / SwapRouter02
        self.router_address = self._checksum(os.getenv("UNISWAP_ROUTER", "0xE592427A0AEce92De3Edee1F18E0157C05861564"))
        self.router_version = os.getenv("UNISWAP_ROUTER_VERSION", "v3").lower()
        router_abi = UNISWAP_ROUTER02_ABI if self.router_version in ("v2", "swaprouter02") else UNISWAP_ROUTER_ABI
        self.router_contract = self.w3.eth.contract(address=self.router_address, abi=router_abi)

        # Uniswap V3 Factory
        self.factory_address = self._checksum(os.getenv("UNISWAP_FACTORY", ""))
        self.factory_contract = None
        if self.factory_address:
            self.factory_contract = self.w3.eth.contract(address=self.factory_address, abi=UNISWAP_FACTORY_ABI)

        # Uniswap Quoter (for on-chain price estimates)
        self.quoter_address = self._checksum(os.getenv("UNISWAP_QUOTER", "0x0000000000000000000000000000000000000000"))
        self.quoter_contract = None
        if self.quoter_address and self.quoter_address != "0x0000000000000000000000000000000000000000":
            self.quoter_contract = self.w3.eth.contract(address=self.quoter_address, abi=UNISWAP_QUOTER_ABI)
        
        # Token addresses (override via env to match your chain)
        self.tokens = {
            "WETH": os.getenv("TOKEN_WETH", os.getenv("TOKEN_WMATIC", "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270")),
            "WMATIC": os.getenv("TOKEN_WMATIC", "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"),
            "USDC": os.getenv("TOKEN_USDC", "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"),
            "USDT": os.getenv("TOKEN_USDT", "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"),
            "DAI": os.getenv("TOKEN_DAI", "0x8f3Cf7ad23Cd3CaDbD9735AFf958023D60d76546")
        }

        self.logger.info(f"✅ DEX Trader initialized (router={self.router_address})")

        # Populate common token addresses for the target chain (best-effort)
        if os.getenv("DISABLE_COINGECKO", "false").lower() != "true":
            try:
                self._populate_common_tokens()
            except Exception as e:
                self.logger.debug(f"Token auto-populate skipped: {e}")

        # Merge allowlist token addresses (if provided)
        try:
            self._load_allowlist_tokens()
        except Exception as e:
            self.logger.debug(f"Allowlist merge skipped: {e}")

    def resolve_token(self, token_identifier: str) -> Tuple[Optional[str], bool]:
        """Resolve a token symbol or address to (address, is_native).

        Returns (address, is_native). If is_native is True the token is the chain's native currency.
        """
        if not token_identifier:
            return (None, False)

        # If caller passed a symbol
        key = str(token_identifier).upper()
        if key in self.tokens and self.tokens[key] and self.tokens[key] != "0x0000000000000000000000000000000000000000":
            addr = self._checksum(self.tokens[key])
            return (addr, False)

        # Common native markers
        if key in ("ETH", "NATIVE", "ETH_NATIVE"):
            return (None, True)

        # If it's an address
        if isinstance(token_identifier, str) and token_identifier.startswith("0x") and len(token_identifier) == 42:
            addr = self._checksum(token_identifier)
            return (addr, False)

        # Default: unresolved token
        return (None, False)

    def _populate_common_tokens(self):
        """Attempt to auto-fill common token addresses on the configured chain using CoinGecko.

        This is a best-effort lookup: it matches symbols to CoinGecko IDs and reads the
        `platforms` mapping for the 'base' chain. Results are merged into `self.tokens`.
        """
        cg_list_url = "https://api.coingecko.com/api/v3/coins/list"
        try:
            resp = requests.get(cg_list_url, timeout=10)
            resp.raise_for_status()
            coins = resp.json()
        except Exception as e:
            self.logger.warning(f"⚠️ Could not fetch CoinGecko coin list: {e}")
            return

        # Build a symbol -> id map (take first occurrence)
        symbol_map = {}
        for c in coins:
            sym = c.get('symbol', '').upper()
            if sym and sym not in symbol_map:
                symbol_map[sym] = c['id']

        common_symbols = [
            "USDC", "USDT", "DAI", "WETH", "WBTC", "LINK", "UNI", "AAVE", "SUSHI", "FRAX",
            "USDC.e", "USDC_NATIVE", "USDC.WORMHOLE", "WBTC", "USDC-OLD"
        ]

        for sym in common_symbols:
            key = sym.upper()
            cg_id = symbol_map.get(key)
            if not cg_id:
                continue

            # Query coin details
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{cg_id}?localization=false"
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
                platforms = data.get('platforms', {}) or {}

                # CoinGecko uses 'base' as the key for Base mainnet when present
                addr = platforms.get('base') or platforms.get('base-mainnet') or platforms.get('base-chain')
                if addr:
                    self.tokens[key] = addr
                    self.logger.info(f"🔎 Resolved {key} -> {addr} via CoinGecko")
                    # Small delay to avoid rate limits
                    time.sleep(0.2)
            except Exception:
                continue

    def _load_allowlist_tokens(self) -> None:
        """Load symbol->address mappings from allowlist file if present."""
        allowlist_path = os.getenv("ALLOWLIST_FILE")
        if allowlist_path and not os.path.isabs(allowlist_path):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            allowlist_path = os.path.join(project_root, allowlist_path)

        if not allowlist_path or not os.path.exists(allowlist_path):
            return

        try:
            import json
            with open(allowlist_path, "r") as f:
                data = json.load(f)
        except Exception:
            return

        tokens = data.get("tokens") if isinstance(data, dict) else data
        if not isinstance(tokens, list):
            return

        for item in tokens:
            if isinstance(item, dict):
                symbol = str(item.get("symbol", "")).upper()
                address = item.get("address")
                if symbol and address:
                    self.tokens[symbol] = address

    def get_token_decimals(self, token_address: str) -> int:
        """Get token decimal places"""
        try:
            addr = self._checksum(token_address)
            cached = self.decimals_cache.get(addr)
            if cached is not None:
                return cached
            contract = self.w3.eth.contract(address=addr, abi=ERC20_ABI)
            # Use wallet retry helper if available
            if hasattr(self.wallet, '_retry_rpc'):
                decimals = self.wallet._retry_rpc(contract.functions.decimals().call)
            else:
                decimals = contract.functions.decimals().call()
            self.decimals_cache.set(addr, decimals)
            return decimals
        except Exception as e:
            self.logger.error(f"❌ Failed to get decimals for {token_address}: {e}")
            return 18  # Default to 18

    def approve_token(self, token_address: str, amount: float) -> Optional[str]:
        """Approve token spending by router"""
        try:
            # Resolve symbol/address; skip approval for native
            addr, is_native = self.resolve_token(token_address)
            if is_native or not addr:
                return None

            decimals = self.get_token_decimals(addr)
            amount_wei = int(amount * (10 ** decimals))

            addr = self._checksum(addr)
            contract = self.w3.eth.contract(address=addr, abi=ERC20_ABI)

            # Check current allowance
            if hasattr(self.wallet, '_retry_rpc'):
                allowance = self.wallet._retry_rpc(contract.functions.allowance(self.wallet.wallet_address, self.router_address).call)
            else:
                allowance = contract.functions.allowance(self.wallet.wallet_address, self.router_address).call()

            if allowance >= amount_wei:
                self.logger.info(f"✅ Already approved: {amount} tokens")
                return None

            # Build approval tx
            tx = contract.functions.approve(
                self.router_address,
                amount_wei * 2  # Approve 2x to avoid repeated approvals
            ).build_transaction({
                "from": self.wallet.wallet_address,
                "chainId": self.wallet.chain_id,
                "gasPrice": self.w3.eth.gas_price,
            })

            self.logger.info(f"🔓 Approving {amount} tokens...")
            return self.wallet.send_transaction(tx)
        except Exception as e:
            self.logger.error(f"❌ Approval failed: {e}")
            return None

    def swap_tokens(
        self,
        token_in: str,
        token_out: str,
        amount_in: float,
        min_amount_out: float = 0.0,
        fee: Optional[int] = None
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Swap tokens on Uniswap V3
        
        Args:
            token_in: Token address to swap FROM
            token_out: Token address to swap TO
            amount_in: Amount of input token
            min_amount_out: Minimum output (slippage protection)
            fee: Pool fee tier (500, 3000, or 10000)
        
        Returns:
            (tx_hash, output_amount)
        """
        try:
            # Resolve tokens (symbol or address)
            addr_in, in_is_native = self.resolve_token(token_in)
            addr_out, out_is_native = self.resolve_token(token_out)

            if (not addr_in and not in_is_native) or (not addr_out and not out_is_native):
                return 0.0

            # Enforce explicit resolution; avoid native->native swaps
            if (not addr_in and not in_is_native) or (not addr_out and not out_is_native):
                raise ValueError("Token resolution failed; missing token address")
            if in_is_native and out_is_native:
                raise ValueError("Invalid swap: native-to-native")

            # Determine decimals
            decimals_in = 18 if in_is_native or not addr_in else self.get_token_decimals(addr_in)
            decimals_out = 18 if out_is_native or not addr_out else self.get_token_decimals(addr_out)

            amount_in_wei = int(amount_in * (10 ** decimals_in))
            min_amount_out_wei = int(min_amount_out * (10 ** decimals_out))

            if fee is None:
                fee = self._select_fee(addr_in or self._checksum(self.tokens.get('WETH')),
                                       addr_out or self._checksum(self.tokens.get('WETH')))
            if fee is None:
                self.logger.warning("⚠️ No pool/fee found for token pair; skipping swap")
                return None, None

            self.logger.info(f"🔄 Swapping {amount_in} ({'native' if in_is_native else addr_in[:8]}) → {'native' if out_is_native else addr_out[:8]} (fee={fee})")

            # Approve token if needed (skip for native)
            if not in_is_native and addr_in:
                approve_tx = self.approve_token(addr_in, amount_in)
                if approve_tx:
                    self.logger.info("⏳ Waiting for approval confirmation...")
                    approval_receipt = self.wallet.wait_for_receipt(approve_tx)
                    if not approval_receipt:
                        self.logger.error("❌ Approval failed; aborting swap")
                        return None, None

            # Build swap transaction
            deadline = int(self.w3.eth.get_block("latest")["timestamp"]) + 300  # 5 min

            # If min_out not provided, try on-chain quoter
            quoted_out = None
            if min_amount_out_wei <= 0 and self.quoter_contract:
                quoted_out = self._quote_exact_input(addr_in or self._checksum(self.tokens.get('WETH')),
                                                     addr_out or self._checksum(self.tokens.get('WETH')),
                                                     fee,
                                                     amount_in_wei)
                if quoted_out:
                    slippage = float(os.getenv("MAX_SLIPPAGE_PERCENT", "0.5")) / 100.0
                    min_amount_out_wei = int(quoted_out * (1 - slippage))

            if self.router_version in ("v2", "swaprouter02"):
                params = (
                    addr_in or self._checksum(self.tokens.get('WETH')),
                    addr_out or self._checksum(self.tokens.get('WETH')),
                    fee,
                    self.wallet.wallet_address,
                    amount_in_wei,
                    min_amount_out_wei,
                    0  # sqrtPriceLimitX96 = 0 (no limit)
                )
            else:
                params = (
                    addr_in or self._checksum(self.tokens.get('WETH')),
                    addr_out or self._checksum(self.tokens.get('WETH')),
                    fee,
                    self.wallet.wallet_address,
                    deadline,
                    amount_in_wei,
                    min_amount_out_wei,
                    0  # sqrtPriceLimitX96 = 0 (no limit)
                )

            # Build transaction; for native ETH swaps the router may expect WETH as tokenIn and 'value' set
            tx = self.router_contract.functions.exactInputSingle(
                params
            ).build_transaction({
                "from": self.wallet.wallet_address,
                "chainId": self.wallet.chain_id,
                "gasPrice": self.w3.eth.gas_price,
                "gas": 300000,  # Typical swap gas
            })

            # If swapping native ETH, set tx['value'] to amount_in_wei
            if in_is_native:
                tx['value'] = amount_in_wei
            
            tx_hash = self.wallet.send_transaction(tx)
            if tx_hash:
                self.logger.info(f"⏳ Waiting for swap confirmation...")
                receipt = self.wallet.wait_for_receipt(tx_hash)
                if receipt:
                    if quoted_out:
                        output_amount = quoted_out / (10 ** decimals_out)
                    else:
                        output_amount = min_amount_out
                    self.logger.info(f"✅ Swap confirmed! Output: ~{output_amount}")
                    return tx_hash, output_amount
            
            return None, None
        except Exception as e:
            self.logger.error(f"❌ Swap failed: {e}")
            return None, None

    def _quote_exact_input(self, token_in: str, token_out: str, fee: int, amount_in_wei: int) -> Optional[int]:
        if not self.quoter_contract:
            return None
        try:
            params = (token_in, token_out, fee, amount_in_wei, 0)
            quoted = self.quoter_contract.functions.quoteExactInputSingle(params).call()
            return quoted[0] if isinstance(quoted, (list, tuple)) else quoted
        except Exception:
            try:
                return self.quoter_contract.functions.quoteExactInputSingle(
                    token_in, token_out, fee, amount_in_wei, 0
                ).call()
            except Exception:
                return None

    def _get_pool_price(self, token_in: str, token_out: str, fee: int) -> Optional[float]:
        if not self.factory_contract:
            return None
        try:
            pool = self.factory_contract.functions.getPool(token_in, token_out, fee).call()
            if not pool or pool == "0x0000000000000000000000000000000000000000":
                return None
            pool_contract = self.w3.eth.contract(address=pool, abi=UNISWAP_POOL_ABI)
            token0 = pool_contract.functions.token0().call()
            token1 = pool_contract.functions.token1().call()
            slot0 = pool_contract.functions.slot0().call()
            sqrt_price_x96 = slot0[0]

            ratio = (sqrt_price_x96 ** 2) / (2 ** 192)
            dec0 = self.get_token_decimals(token0)
            dec1 = self.get_token_decimals(token1)
            price_token1_per_token0 = ratio * (10 ** (dec0 - dec1))

            if token_in.lower() == token0.lower() and token_out.lower() == token1.lower():
                return float(price_token1_per_token0)
            if token_in.lower() == token1.lower() and token_out.lower() == token0.lower():
                if price_token1_per_token0 == 0:
                    return None
                return float(1 / price_token1_per_token0)
        except Exception:
            return None
        return None

    def _estimate_output_from_pool(self, token_in: str, token_out: str, amount_in: float) -> Optional[float]:
        for fee in self._fee_tiers():
            price = self._get_pool_price(token_in, token_out, fee)
            if price:
                return amount_in * price
        return None

    def estimate_swap_output(
        self,
        token_in: str,
        token_out: str,
        amount_in: float
    ) -> float:
        """Estimate output amount for a swap (off-chain quote)"""
        try:
            if not self.quoter_contract:
                self.logger.info(f"📊 Estimating swap: {amount_in} → {str(token_out)[:6]} (no quoter)")
                return amount_in * 0.995  # Fallback

            addr_in, in_is_native = self.resolve_token(token_in)
            addr_out, out_is_native = self.resolve_token(token_out)

            addr_in = addr_in or self._checksum(self.tokens.get('WETH'))
            addr_out = addr_out or self._checksum(self.tokens.get('WETH'))

            decimals_in = 18 if in_is_native or not addr_in else self.get_token_decimals(addr_in)
            decimals_out = 18 if out_is_native or not addr_out else self.get_token_decimals(addr_out)

            amount_in_wei = int(amount_in * (10 ** decimals_in))

            fees = self._fee_tiers()
            amount_out_wei = None
            for fee in fees:
                try:
                    params = (addr_in, addr_out, fee, amount_in_wei, 0)
                    quoted = self.quoter_contract.functions.quoteExactInputSingle(params).call()
                    amount_out_wei = quoted[0]
                    break
                except Exception:
                    try:
                        amount_out_wei = self.quoter_contract.functions.quoteExactInputSingle(
                            addr_in, addr_out, fee, amount_in_wei, 0
                        ).call()
                        break
                    except Exception:
                        continue

            if amount_out_wei is None:
                fallback = self._estimate_output_from_pool(addr_in, addr_out, amount_in)
                if fallback:
                    return float(fallback)
                return 0.0

            amount_out = amount_out_wei / (10 ** decimals_out)
            self.logger.info(f"📊 Quoted swap: {amount_in} → {amount_out:.6f}")
            return float(amount_out)
        except Exception as e:
            self.logger.error(f"❌ Quote failed: {e}")
            return 0.0

    def get_price_in_quote(self, token: str, quote: str = "USDC") -> Optional[float]:
        """Return token price in quote currency using on-chain quoter."""
        try:
            token_key = str(token).upper()
            quote_key = str(quote).upper()

            if token_key in ("ETH", "NATIVE"):
                token = "WETH"
                token_key = "WETH"
            if quote_key in ("ETH", "NATIVE"):
                quote = "WETH"
                quote_key = "WETH"

            if token_key == quote_key:
                return 1.0

            price = self.estimate_swap_output(token_in=token, token_out=quote, amount_in=1.0)
            return price if price and price > 0 else None
        except Exception:
            return None

    def _fee_tiers(self) -> list:
        tiers = os.getenv("UNISWAP_FEE_TIERS", "500,3000,10000")
        out = []
        for t in tiers.split(','):
            t = t.strip()
            if t.isdigit():
                out.append(int(t))
        return out or [3000]

    def _select_fee(self, token_in: str, token_out: str) -> Optional[int]:
        # Prefer factory lookup when available
        if self.factory_contract:
            for fee in self._fee_tiers():
                try:
                    pool = self.factory_contract.functions.getPool(token_in, token_out, fee).call()
                    if pool and pool != "0x0000000000000000000000000000000000000000":
                        return fee
                except Exception:
                    continue

        if not self.quoter_contract:
            return None
        for fee in self._fee_tiers():
            try:
                params = (token_in, token_out, fee, 10 ** 6, 0)
                _ = self.quoter_contract.functions.quoteExactInputSingle(params).call()
                return fee
            except Exception:
                try:
                    _ = self.quoter_contract.functions.quoteExactInputSingle(
                        token_in, token_out, fee, 10 ** 6, 0
                    ).call()
                    return fee
                except Exception:
                    continue
        return None

    def _checksum(self, address: Optional[str]) -> Optional[str]:
        if not address:
            return None
        try:
            return Web3.to_checksum_address(address)
        except Exception:
            return address
