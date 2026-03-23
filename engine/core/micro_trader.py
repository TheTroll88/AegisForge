# engine/core/micro_trader.py

import logging
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from web3 import Web3
from .wallet_manager import WalletManager
from .dex_trader import DEXTrader
from .trade_logger import TradeLogger
from core.live_data_feed import LiveDataFeed
from core.allowlist import load_allowlist
from core.config import TraderConfig

load_dotenv()

class MicroTrader:
    """
    Live blockchain trading with micro positions (cents/dollars)
    Perfect for testing before scaling to full amount
    """
    
    def __init__(self, logger=None, trade_logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.trade_logger = trade_logger or TradeLogger()
        
        # Micro trading settings
        self.micro_enabled = os.getenv("MICRO_TRADING_ENABLED", "True").lower() == "true"
        self.base_amount = float(os.getenv("MICRO_TRADING_BASE_AMOUNT", "1.0"))  # Base amount in quote token
        self.scale_factor = float(os.getenv("MICRO_TRADING_SCALE_FACTOR", "0.01"))  # 1% of balance
        self.max_position = float(os.getenv("MICRO_MAX_POSITION_SIZE", "100.0"))  # Max $100 per trade
        self.gas_reserve = float(os.getenv("GAS_RESERVE_ETH", "0.005"))
        self.max_trade_cycles = int(os.getenv("MAX_TRADE_CYCLES", "5"))
        
        # Slippage protection
        self.max_slippage = float(os.getenv("MAX_SLIPPAGE_PERCENT", "0.5"))
        self.min_profit_threshold = float(os.getenv("MIN_PROFIT_THRESHOLD", "0.01"))
        self.min_trade_amount = float(os.getenv("MIN_TRADE_AMOUNT", "0.001"))
        
        # Initialize blockchain components
        try:
            self.wallet = WalletManager(logger=self.logger)
            self.dex = DEXTrader(self.wallet, logger=self.logger)
            self.logger.info("✅ MicroTrader initialized with blockchain connection")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize blockchain: {e}")
            self.wallet = None
            self.dex = None
        
        # Trade tracking
        self.positions = {}
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        # TP/SL settings
        self.tp_percent = getattr(TraderConfig, 'TAKE_PROFIT_PERCENT', float(os.getenv('TAKE_PROFIT_PERCENT', 2.0)))
        self.sl_percent = getattr(TraderConfig, 'STOP_LOSS_PERCENT', float(os.getenv('STOP_LOSS_PERCENT', 1.0)))

        # Allowed token symbols (file-based allowlist + env override)
        self.allowed_tokens = load_allowlist()
        if self.dex and os.getenv("FILTER_ALLOWLIST_POOLS", "true").lower() == "true":
            self.allowed_tokens = self._filter_tokens_with_pools(self.allowed_tokens)

    def _normalize_token_id(self, token_id: str) -> str:
        token_id = str(token_id).strip()
        if token_id.startswith("0x") and len(token_id) == 42:
            try:
                return Web3.to_checksum_address(token_id)
            except Exception:
                return token_id
        return token_id.upper()

    def _filter_tokens_with_pools(self, tokens):
        quote = os.getenv("FILTER_ALLOWLIST_QUOTE", os.getenv("DEFAULT_QUOTE_TOKEN", "USDC"))
        quote_addr, quote_is_native = self.dex.resolve_token(quote)
        if quote_is_native:
            quote_addr = self.dex._checksum(self.dex.tokens.get("WETH"))
        if not quote_addr:
            return tokens

        filtered = []
        for t in tokens:
            token_id = self._normalize_token_id(t)
            addr, is_native = self.dex.resolve_token(token_id)
            if is_native:
                addr = self.dex._checksum(self.dex.tokens.get("WETH"))
            if not addr:
                continue
            if addr.lower() == quote_addr.lower():
                filtered.append(token_id)
                continue
            fee = self.dex._select_fee(addr, quote_addr)
            if fee is not None:
                filtered.append(token_id)

        if filtered:
            self.logger.info(f"✅ Allowlist filtered to {len(filtered)} pool-backed tokens")
            return filtered
        self.logger.warning("⚠️ Pool filter produced no tokens; using original allowlist")
        return tokens

    def calculate_position_size(self, token_price: float) -> float:
        """Calculate position size based on balance and strategy"""
        if not self.micro_enabled or not self.wallet:
            return 0.0
        
        try:
            quote_symbol = os.getenv("DEFAULT_QUOTE_TOKEN", "USDC").upper()

            # Always keep a gas reserve in native ETH
            eth_balance = float(self.wallet.get_balance())
            eth_available = max(0.0, eth_balance - self.gas_reserve)
            if eth_available <= 0:
                self.logger.warning("⚠️ ETH balance below gas reserve; skipping trade sizing")
                return 0.0

            if quote_symbol in ("ETH", "NATIVE"):
                # Position sizing in ETH
                position_1pct = eth_available * self.scale_factor
                desired = max(self.base_amount, position_1pct)
                position_size = min(desired, eth_available, self.max_position)
                self.logger.info(f"💰 Position size: {position_size:.6f} ETH (ETH bal: {eth_balance:.6f}, reserve: {self.gas_reserve})")
                return position_size

            # Quote token is USD-stable; compute USD-equivalent balance from ETH
            eth_price = None
            if self.dex:
                eth_price = self.dex.get_price_in_quote("WETH", quote_symbol)
            if not eth_price:
                feed = LiveDataFeed()
                eth_price = feed.get_price(f"WETH/{quote_symbol}") or 0
            quote_balance = eth_available * (eth_price or 0)

            # Calculate position: 1% of balance or base amount (quote token), whichever is smaller
            position_1pct = quote_balance * self.scale_factor
            position_size = min(self.base_amount, position_1pct, self.max_position)

            self.logger.info(f"💰 Position size: {position_size:.4f} {quote_symbol} (ETH bal: {eth_balance:.6f}, ETH price: {eth_price})")
            return position_size
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate position: {e}")
            return self.base_amount

    def execute_buy(
        self,
        symbol: str,
        price: float,
        strategy_name: str = "unknown"
    ) -> Optional[dict]:
        """Execute a BUY trade on blockchain"""
        if not self.wallet or not self.dex:
            self.logger.warning("⚠️ Blockchain not available - paper mode")
            return self._paper_trade_buy(symbol, price, strategy_name)
        
        try:
            symbol = self._normalize_token_id(symbol)

            if self.max_trade_cycles > 0 and self.total_trades >= self.max_trade_cycles:
                self.logger.info("🛑 Max trade cycles reached; skipping new buys")
                return None

            # Enforce allowed token list
            if symbol not in self.allowed_tokens:
                self.logger.warning(f"⚠️ Symbol {symbol} not in allowed tokens; skipping buy")
                return None

            if self.wallet and self.wallet.pending_tx_count() > 0:
                self.logger.warning("⚠️ Pending transaction(s) detected; skipping buy")
                return None

            position_size = self.calculate_position_size(price)
            # Allow very small positions (cents). Minimum execution threshold lowered.
            if position_size < self.min_trade_amount:
                quote_symbol = os.getenv("DEFAULT_QUOTE_TOKEN", "USDC")
                self.logger.warning(f"⚠️ Position too small: {position_size} {quote_symbol}")
                return None
            
            # Prepare token swap: USDC (symbol) → target token (symbol/address)
            usdc_symbol = os.getenv("DEFAULT_QUOTE_TOKEN", "USDC")
            target_token = symbol  # let DEXTrader resolve symbol or accept address

            # Ensure target token resolves before trading
            addr, is_native = self.dex.resolve_token(target_token)
            if not addr and not is_native:
                self.logger.warning(f"⚠️ Unresolved token {symbol}; skipping buy")
                return None
            
            # Calculate min output with slippage (or defer to on-chain quoter)
            estimated_output = position_size / price
            use_quoter_min = os.getenv("USE_QUOTER_MIN_OUT", "true").lower() == "true"
            min_output = 0.0 if use_quoter_min else estimated_output * (1 - self.max_slippage / 100)
            
            self.logger.info(f"🟩 BUY {symbol}: ${position_size:.4f} @ ${price:.6f}")
            
            # Execute swap
            tx_hash, output = self.dex.swap_tokens(
                token_in=usdc_symbol,
                token_out=target_token,
                amount_in=position_size,
                min_amount_out=min_output
            )
            
            if tx_hash:
                trade = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "symbol": symbol,
                    "action": "buy",
                    "price": price,
                    "amount": position_size,
                    "output_amount": output or estimated_output,
                    "strategy": strategy_name,
                    "tx_hash": tx_hash,
                    "mode": "LIVE_MICRO",
                    "roi": 0.0
                }
                
                self.positions[symbol] = {
                    "entry_price": price,
                    "amount": output or estimated_output,
                    "entry_time": datetime.utcnow().isoformat(),
                    "strategy": strategy_name
                }
                
                self.trade_logger.log_simple(trade)
                self.logger.info(f"✅ BUY executed: TX {tx_hash[:10]}...")
                return trade
        
        except Exception as e:
            self.logger.error(f"❌ BUY failed: {e}")
        
        return None

    def _tune_risk(self) -> None:
        if self.total_trades < 5 or self.total_trades % 5 != 0:
            return
        win_rate = self.winning_trades / max(1, self.total_trades)
        tp = self.tp_percent
        sl = self.sl_percent

        if win_rate >= 0.6:
            tp = min(3.0, tp + 0.25)
            sl = min(1.5, sl + 0.25)
        elif win_rate <= 0.4:
            tp = max(1.0, tp - 0.25)
            sl = max(0.5, sl - 0.25)

        if tp != self.tp_percent or sl != self.sl_percent:
            self.tp_percent = tp
            self.sl_percent = sl
            self.logger.info(f"🧠 Tuned TP/SL: TP={tp:.2f}% SL={sl:.2f}% (win_rate={win_rate:.2f})")

    def execute_sell(
        self,
        symbol: str,
        price: float,
        strategy_name: str = "unknown"
    ) -> Optional[dict]:
        """Execute a SELL trade on blockchain"""
        if not self.wallet or not self.dex:
            return self._paper_trade_sell(symbol, price, strategy_name)
        
        symbol = self._normalize_token_id(symbol)

        if symbol not in self.positions:
            self.logger.warning(f"⚠️ No position to sell: {symbol}")
            return None
        
        try:
            if self.wallet and self.wallet.pending_tx_count() > 0:
                self.logger.warning("⚠️ Pending transaction(s) detected; skipping sell")
                return None
            position = self.positions[symbol]
            entry_price = position["entry_price"]
            amount = position["amount"]
            
            # Calculate PnL
            profit = amount * (price - entry_price)
            roi = ((price - entry_price) / entry_price) * 100
            
            # Use symbol/address resolution in DEX trader; quote token symbol
            target_token = symbol
            usdc_symbol = os.getenv("DEFAULT_QUOTE_TOKEN", "USDC")
            
            # Sell back to USDC
            estimated_output = amount * price
            min_output = estimated_output * (1 - self.max_slippage / 100)
            
            self.logger.info(f"🟥 SELL {symbol}: {amount:.6f} @ ${price:.6f} | ROI: {roi:.2f}%")
            
            # Execute swap back to USDC
            tx_hash, output = self.dex.swap_tokens(
                token_in=target_token,
                token_out=usdc_symbol,
                amount_in=amount,
                min_amount_out=min_output
            )
            
            if tx_hash:
                trade = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "symbol": symbol,
                    "action": "sell",
                    "price": price,
                    "amount": amount,
                    "profit": profit,
                    "roi": roi,
                    "strategy": strategy_name,
                    "tx_hash": tx_hash,
                    "mode": "LIVE_MICRO",
                    "result": "win" if profit > 0 else "loss"
                }
                
                if profit > 0:
                    self.winning_trades += 1
                    self.logger.info(f"🏆 WIN: ${profit:.4f} | TX: {tx_hash[:10]}...")
                else:
                    self.losing_trades += 1
                    self.logger.info(f"💔 LOSS: ${profit:.4f} | TX: {tx_hash[:10]}...")
                
                self.total_trades += 1
                self.total_pnl += profit
                del self.positions[symbol]

                self.trade_logger.log(trade)
                self._tune_risk()
                return trade
        
        except Exception as e:
            self.logger.error(f"❌ SELL failed: {e}")
        
        return None

    def execute(
        self,
        signal: dict,
        market_data: dict,
        strategy_name: str = "unknown"
    ) -> Optional[dict]:
        """Execute a trading signal"""
        action = signal.get("action", "hold")
        symbol = market_data.get("symbol", "UNKNOWN")
        price = market_data.get("price", 0)

        if action == "buy" and self.max_trade_cycles > 0 and self.total_trades >= self.max_trade_cycles:
            self.logger.info("🛑 Max trade cycles reached; ignoring buy signal")
            return None
        
        if action == "buy":
            return self.execute_buy(symbol, price, strategy_name)
        elif action == "sell":
            return self.execute_sell(symbol, price, strategy_name)
        else:
            return None

    def _paper_trade_buy(self, symbol: str, price: float, strategy: str) -> dict:
        """Fallback paper trade when blockchain unavailable"""
        self.positions[symbol] = {
            "entry_price": price,
            "amount": self.base_amount / price,
            "entry_time": datetime.utcnow().isoformat(),
            "strategy": strategy
        }
        
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "action": "buy",
            "price": price,
            "amount": self.base_amount,
            "strategy": strategy,
            "mode": "PAPER_FALLBACK"
        }
        return trade

    def _paper_trade_sell(self, symbol: str, price: float, strategy: str) -> Optional[dict]:
        """Fallback paper trade when blockchain unavailable"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        profit = position["amount"] * (price - position["entry_price"])
        roi = ((price - position["entry_price"]) / position["entry_price"]) * 100
        
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "action": "sell",
            "price": price,
            "amount": position["amount"],
            "profit": profit,
            "roi": roi,
            "strategy": strategy,
            "mode": "PAPER_FALLBACK",
            "result": "win" if profit > 0 else "loss"
        }
        
        del self.positions[symbol]
        self.total_pnl += profit
        return trade

    def get_stats(self) -> dict:
        """Get trading statistics"""
        total = self.winning_trades + self.losing_trades
        win_rate = (self.winning_trades / total * 100) if total > 0 else 0
        
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "total_pnl": self.total_pnl,
            "open_positions": len(self.positions),
            "micro_trading_enabled": self.micro_enabled,
            "base_position_size": self.base_amount
        }

    def check_positions(self) -> None:
        """Check open positions for TP/SL and close them if limits hit."""
        if not self.positions:
            return

        quote_symbol = os.getenv("DEFAULT_QUOTE_TOKEN", "USDC")

        for symbol, pos in list(self.positions.items()):
            try:
                # Estimate current price in quote token for 1 unit
                current_price = self.dex.estimate_swap_output(token_in=symbol, token_out=quote_symbol, amount_in=1)
                entry_price = pos.get('entry_price', None)
                if not entry_price or current_price <= 0:
                    continue

                change_pct = ((current_price - entry_price) / entry_price) * 100
                target = self.tp_percent
                stop = -abs(self.sl_percent)

                if change_pct >= target:
                    self.logger.info(f"🔔 TP hit for {symbol}: change {change_pct:.2f}% >= {target}%")
                    self.execute_sell(symbol, current_price, strategy_name=pos.get('strategy'))
                elif change_pct <= stop:
                    self.logger.info(f"⚠️ SL hit for {symbol}: change {change_pct:.2f}% <= {stop}%")
                    self.execute_sell(symbol, current_price, strategy_name=pos.get('strategy'))
                else:
                    self.logger.debug(f"{symbol}: change {change_pct:.2f}% — waiting")
            except Exception as e:
                self.logger.error(f"Error checking position {symbol}: {e}")
