"""Aggregate common token addresses for Base via CoinGecko and verify on-chain.

Usage: run from `kratos_core`:
  python scripts/aggregate_and_vet.py

This script will:
- Query CoinGecko for common symbols and attempt to find a 'base' platform address.
- Verify the address has contract code on your configured RPC (via WalletManager).
- Test for ERC20 decimals to ensure it's a token contract.
- Write a proposed env file `proposed_base_env_vetted.txt` for your review.
"""

import time
import os
import sys
import pathlib
import requests
import json

# Ensure core package imports work when running from scripts/
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.wallet_manager import WalletManager

COMMON_SYMBOLS = [
    "USDC", "USDT", "DAI", "WETH", "WBTC", "LINK", "UNI", "AAVE", "SUSHI", "FRAX"
]

CG_LIST_URL = "https://api.coingecko.com/api/v3/coins/list"

# Tokenlist endpoints for Base
TOKENLISTS = {
    "Uniswap": "https://static.optimism.io/base.tokenlist.json",
    "1inch": "https://tokens.1inch.io/v1.2/137/tokenlist.json",  # 1inch does not have a Base list, fallback to Polygon for now
    "SushiSwap": "https://token-list.sushi.com/base.json"
}

def build_symbol_map(retries=3):
    for i in range(retries):
        try:
            r = requests.get(CG_LIST_URL, timeout=15)
            r.raise_for_status()
            coins = r.json()
            sym = {}
            for c in coins:
                s = c.get('symbol')
                if s:
                    k = s.upper()
                    if k not in sym:
                        sym[k] = c['id']
            return sym
        except Exception as e:
            wait = 1.5 ** i
            print(f"CoinGecko list fetch failed ({e}), retrying in {wait:.1f}s")
            time.sleep(wait)
    return {}

def fetch_cg_platform_address(cg_id):
    url = f"https://api.coingecko.com/api/v3/coins/{cg_id}?localization=false"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    platforms = data.get('platforms') or {}
    # Try common keys
    for key in ('base', 'base-mainnet', 'basechain', 'base-chain'):
        addr = platforms.get(key)
        if addr:
            return addr
    for k,v in platforms.items():
        if 'base' in k.lower() and v:
            return v
    return None

def verify_on_chain(wallet, address):
    try:
        if not address or not address.startswith('0x'):
            return False, 'invalid'
        code = wallet.w3.eth.get_code(address)
        if code in (b'', '0x'):
            return False, 'no-code'
        # Check ERC20 decimals
        from core.dex_trader import ERC20_ABI
        contract = wallet.w3.eth.contract(address=address, abi=ERC20_ABI)
        try:
            decimals = contract.functions.decimals().call()
            return True, f'decimals:{decimals}'
        except Exception as e:
            return False, f'no-decimals:{e}'
    except Exception as e:
        return False, str(e)


def fetch_tokenlist(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        tokens = data.get('tokens', [])
        return tokens
    except Exception as e:
        print(f"Failed to fetch tokenlist {url}: {e}")
        return []

def aggregate_tokenlists():
    symbol_map = {}
    for name, url in TOKENLISTS.items():
        tokens = fetch_tokenlist(url)
        for t in tokens:
            symbol = t.get('symbol', '').upper()
            address = t.get('address')
            if symbol and address and symbol not in symbol_map:
                symbol_map[symbol] = {
                    'address': address,
                    'source': name
                }
    return symbol_map

def main():
    print('🔎 Aggregating candidate tokens from CoinGecko and public tokenlists...')
    symmap = build_symbol_map()
    wallet = WalletManager()

    # Aggregate from tokenlists
    tokenlist_map = aggregate_tokenlists()

    results = {}
    for s in COMMON_SYMBOLS:
        cg_id = symmap.get(s)
        addr = None
        status = ''
        # Try CoinGecko first
        if cg_id:
            try:
                addr = fetch_cg_platform_address(cg_id)
            except Exception as e:
                status = f'cg-fetch-error:{e}'
        if not addr:
            # Try tokenlists
            tokenlist_entry = tokenlist_map.get(s)
            if tokenlist_entry:
                addr = tokenlist_entry['address']
                status = f"from-tokenlist:{tokenlist_entry['source']}"
            else:
                status = status or 'not-on-base'

        if not addr:
            results[s] = {'address': None, 'status': status}
            time.sleep(0.2)
            continue

        ok, info = verify_on_chain(wallet, addr)
        results[s] = {'address': addr, 'status': info if ok else f'fail:{info}'}
        print(f"{s}: {addr} — {results[s]['status']}")
        time.sleep(0.25)

    # Write proposed vetted env
    lines = ['# Proposed token env entries (AUTO-GENERATED, review carefully)']
    for s, v in results.items():
        key = f"TOKEN_{s}"
        val = v.get('address') or ''
        lines.append(f"{key}={val}  # status={v.get('status')}")

    out = os.path.join(os.path.dirname(__file__), 'proposed_base_env_vetted.txt')
    with open(out, 'w') as f:
        f.write('\n'.join(lines))

    print('\n✅ Wrote proposal to', out)
    print('\nPreview:')
    print('\n'.join(lines))

if __name__ == '__main__':
    main()
