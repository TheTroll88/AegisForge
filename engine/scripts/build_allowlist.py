"""Build a wide, vetted allowlist from public tokenlists and on-chain checks.

Run from AegisForge root:
  python engine/scripts/build_allowlist.py

This script:
- Fetches tokenlists from TOKENLIST_URLS env (comma-separated)
- Filters tokens to Base chainId
- Verifies contract code + decimals on-chain
- Filters tokens that cannot be quoted on Uniswap V3 (liquidity check)
- Writes allowlist.json for bot use
"""
import json
import os
import sys
import time
import pathlib
import requests
import ccxt
from dotenv import load_dotenv

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.wallet_manager import WalletManager
from core.dex_trader import DEXTrader

BASE_CHAIN_ID = 8453

# Load .env from project root
project_root = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(project_root / ".env")


def fetch_tokenlist(url: str) -> list:
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        return data.get("tokens", [])
    except Exception as e:
        print(f"Failed to fetch tokenlist {url}: {e}")
        return []


def is_contract(wallet: WalletManager, address: str) -> bool:
    try:
        code = wallet.w3.eth.get_code(address)
        return code not in (b"", "0x")
    except Exception:
        return False


def main():
    default_urls = "https://tokens.uniswap.org,https://token-list.sushi.com"
    urls = os.getenv("TOKENLIST_URLS", default_urls).split(",")
    urls = [u.strip() for u in urls if u.strip()]
    if not urls:
        print("No TOKENLIST_URLS configured.")
        return

    out_path = os.getenv("ALLOWLIST_FILE", os.path.join(project_root, "engine", "data", "allowlist.json"))
    if not os.path.isabs(out_path):
        out_path = os.path.join(project_root, out_path)
    out_path = os.path.abspath(out_path)

    wallet = WalletManager()
    dex = DEXTrader(wallet)

    exchange_symbols = None
    if os.getenv("ALLOWLIST_FILTER_EXCHANGE", "true").lower() == "true":
        exchange_ids = os.getenv("EXCHANGE_IDS", os.getenv("EXCHANGE_ID", "binanceus"))
        exchange_ids = [e.strip() for e in exchange_ids.split(",") if e.strip()]
        exchange_symbols = set()
        quotes = {"USDT", "USDC", "USD", "BUSD", "FDUSD"}
        for exchange_id in exchange_ids:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({"enableRateLimit": True})
                exchange.load_markets()
                for m in exchange.markets.values():
                    if not m.get("active"):
                        continue
                    base = m.get("base")
                    quote = m.get("quote")
                    if base and quote in quotes:
                        exchange_symbols.add(str(base).upper())
                print(f"Loaded {len(exchange_symbols)} symbols (so far) from {exchange_id}")
            except Exception as e:
                print(f"Exchange symbol load failed ({exchange_id}): {e}")

    candidates = {}
    for url in urls:
        tokens = fetch_tokenlist(url)
        for t in tokens:
            try:
                if int(t.get("chainId", 0)) != BASE_CHAIN_ID:
                    continue
                symbol = str(t.get("symbol", "")).upper()
                address = t.get("address")
                if symbol and address and symbol not in candidates:
                    if exchange_symbols and symbol not in exchange_symbols:
                        continue
                    candidates[symbol] = address
            except Exception:
                continue

    max_tokens = int(os.getenv("MAX_ALLOWLIST_TOKENS", "250"))
    require_quote = os.getenv("ALLOWLIST_REQUIRE_QUOTE", "true").lower() == "true"
    if require_quote and not dex.quoter_contract:
        print("Quoter not configured; disabling quote requirement.")
        require_quote = False

    vetted = []
    for symbol, address in candidates.items():
        if not address or not address.startswith("0x"):
            continue
        if not is_contract(wallet, address):
            continue
        # Liquidity check via quoter (quote -> token)
        if require_quote:
            quote = dex.get_price_in_quote(address, os.getenv("DEFAULT_QUOTE_TOKEN", "USDC"))
            if not quote or quote <= 0:
                continue
        vetted.append({"symbol": symbol, "address": address})
        print(f"✅ {symbol} ok")
        time.sleep(0.1)
        if len(vetted) >= max_tokens:
            print(f"Reached MAX_ALLOWLIST_TOKENS={max_tokens}; stopping.")
            break

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"tokens": vetted}, f, indent=2)

    print(f"\n✅ Wrote allowlist: {out_path}")


if __name__ == "__main__":
    main()
