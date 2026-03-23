#!/usr/bin/env python3
"""Diagnose on-chain pricing for a token pair.

Usage:
  python scripts/diagnose_quoter.py --base WETH --quote USDC
  python scripts/diagnose_quoter.py --base 0x... --quote 0x... --amount 1.0
"""

import argparse
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.wallet_manager import WalletManager
from core.dex_trader import DEXTrader


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Uniswap V3 quoter")
    parser.add_argument("--base", required=True, help="token in (symbol or address)")
    parser.add_argument("--quote", required=True, help="token out (symbol or address)")
    parser.add_argument("--amount", type=float, default=1.0, help="amount in base token")
    args = parser.parse_args()

    wallet = WalletManager()
    dex = DEXTrader(wallet)

    base_addr, base_is_native = dex.resolve_token(args.base)
    quote_addr, quote_is_native = dex.resolve_token(args.quote)

    if base_is_native:
        base_addr = dex._checksum(dex.tokens.get("WETH"))
    if quote_is_native:
        quote_addr = dex._checksum(dex.tokens.get("WETH"))

    if not base_addr or not quote_addr:
        print("Failed to resolve base/quote tokens.")
        return 1

    print(f"Base:  {args.base} -> {base_addr}")
    print(f"Quote: {args.quote} -> {quote_addr}")

    tiers = dex._fee_tiers()
    print(f"Fee tiers: {tiers}")

    pool_found = False
    if dex.factory_contract:
        for fee in tiers:
            try:
                pool = dex.factory_contract.functions.getPool(base_addr, quote_addr, fee).call()
                if pool and pool != "0x0000000000000000000000000000000000000000":
                    print(f"Pool found for fee {fee}: {pool}")
                    pool_found = True
            except Exception as e:
                print(f"Pool check failed for fee {fee}: {e}")
    else:
        print("Factory contract not configured; skipping pool lookup.")

    amount_in_wei = int(args.amount * (10 ** dex.get_token_decimals(base_addr)))
    if dex.quoter_contract:
        for fee in tiers:
            try:
                params = (base_addr, quote_addr, fee, amount_in_wei, 0)
                quoted = dex.quoter_contract.functions.quoteExactInputSingle(params).call()
                amount_out = quoted[0] if isinstance(quoted, (list, tuple)) else quoted
                print(f"Quote ok fee={fee}: {amount_out}")
            except Exception as e:
                try:
                    amount_out = dex.quoter_contract.functions.quoteExactInputSingle(
                        base_addr, quote_addr, fee, amount_in_wei, 0
                    ).call()
                    print(f"Quote ok fee={fee}: {amount_out}")
                except Exception as e2:
                    print(f"Quote failed fee={fee}: {e2}")
    else:
        print("Quoter contract not configured.")

    if not pool_found:
        print("No pools found for any fee tier.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
