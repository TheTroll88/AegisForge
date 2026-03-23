import os
from web3 import Web3
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    rpc_url = os.getenv("METAMASK_RPC_URL")
    wallet_address = os.getenv("METAMASK_WALLET_ADDRESS")

    if not rpc_url:
        raise SystemExit("METAMASK_RPC_URL not set")
    if not wallet_address:
        raise SystemExit("METAMASK_WALLET_ADDRESS not set")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise SystemExit(f"RPC not reachable: {rpc_url}")

    balance_wei = w3.eth.get_balance(wallet_address)
    balance_eth = w3.from_wei(balance_wei, "ether")

    print(f"RPC: {rpc_url}")
    print(f"Address: {wallet_address}")
    print(f"Balance (ETH): {balance_eth}")


if __name__ == "__main__":
    main()
