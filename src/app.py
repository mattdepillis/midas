from fetchers.coinbase import CoinbaseRequestHandler

def main():
    print("Welcome to Midas 🪙\n")
    coinbase = CoinbaseRequestHandler()
    portfolio = coinbase.get_holdings()

    for asset in portfolio:
        print("\n", asset)

if __name__ == "__main__":
    main()