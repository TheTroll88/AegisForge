"""Simple helper to print resolved token addresses using DEXTrader.

Run from AegisForge root:

python engine/scripts/print_resolved_tokens.py
"""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.wallet_manager import WalletManager
from core.dex_trader import DEXTrader
import os

def main():
    wm = WalletManager()
    dex = DEXTrader(wm)

    tokens = os.getenv('DEFAULT_ALLOWED_TOKENS')
    if tokens:
        symbols = [s.strip().upper() for s in tokens.split(',') if s.strip()]
    else:
        symbols = ["WETH","USDC","USDT","DAI","WBTC","LINK","UNI","AAVE","SUSHI","FRAX"]

    print('Resolved tokens:')
    for sym in symbols:
        addr, is_native = dex.resolve_token(sym)
        print(f"{sym}: {'native' if is_native else addr}")

if __name__ == '__main__':
    main()
