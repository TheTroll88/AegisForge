from core.live_data_feed import LiveDataFeed

def main():
    feed = LiveDataFeed()
    price = feed.get_price("WETH/USDC")
    if price:
        print("✅ On-chain price fetched:")
        print(price)
    else:
        print("❌ Failed to fetch on-chain price.")

if __name__ == "__main__":
    main()
