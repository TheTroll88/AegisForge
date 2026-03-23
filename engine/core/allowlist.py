import json
import os
from typing import List
from web3 import Web3

def load_allowlist() -> List[str]:
    """Load allowed tokens from file and env override."""
    tokens = []

    allowlist_file = os.getenv("ALLOWLIST_FILE")
    if allowlist_file:
        if not os.path.isabs(allowlist_file):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            allowlist_file = os.path.join(project_root, allowlist_file)

    if allowlist_file and os.path.exists(allowlist_file):
        try:
            with open(allowlist_file, "r") as f:
                data = json.load(f)
            if isinstance(data, dict) and "tokens" in data:
                for t in data.get("tokens", []):
                    if isinstance(t, dict):
                        sym = t.get("symbol")
                        if sym:
                            tokens.append(str(sym).upper())
                        else:
                            addr = t.get("address")
                            if isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42:
                                try:
                                    tokens.append(Web3.to_checksum_address(addr))
                                except Exception:
                                    tokens.append(addr)
                    else:
                        raw = str(t)
                        if raw.startswith("0x") and len(raw) == 42:
                            try:
                                tokens.append(Web3.to_checksum_address(raw))
                            except Exception:
                                tokens.append(raw)
                        else:
                            tokens.append(raw.upper())
            elif isinstance(data, list):
                for t in data:
                    if isinstance(t, dict):
                        sym = t.get("symbol")
                        if sym:
                            tokens.append(str(sym).upper())
                        else:
                            addr = t.get("address")
                            if isinstance(addr, str) and addr.startswith("0x") and len(addr) == 42:
                                try:
                                    tokens.append(Web3.to_checksum_address(addr))
                                except Exception:
                                    tokens.append(addr)
                    else:
                        raw = str(t)
                        if raw.startswith("0x") and len(raw) == 42:
                            try:
                                tokens.append(Web3.to_checksum_address(raw))
                            except Exception:
                                tokens.append(raw)
                        else:
                            tokens.append(raw.upper())
        except Exception:
            pass

    env_tokens = os.getenv("DEFAULT_ALLOWED_TOKENS")
    if env_tokens:
        for s in env_tokens.split(","):
            s = s.strip()
            if not s:
                continue
            if s.startswith("0x") and len(s) == 42:
                try:
                    tokens.append(Web3.to_checksum_address(s))
                except Exception:
                    tokens.append(s)
            else:
                tokens.append(s.upper())

    if not tokens:
        tokens = ["WETH", "USDC", "USDT", "DAI", "WBTC", "LINK", "UNI", "AAVE", "SUSHI", "FRAX"]

    max_tokens = int(os.getenv("MAX_TRADE_TOKENS", "200"))

    # De-duplicate preserving order
    seen = set()
    result = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            result.append(t)
        if len(result) >= max_tokens:
            break
    return result
