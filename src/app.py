from fetchers.coinbase import get_coinbase_holdings

def main():
    print("Welcome to Midas 🪙\n")
    portfolio = get_coinbase_holdings()
    # for asset in portfolio:
    #     print(f"{asset['currency']}: {asset['balance']}")

if __name__ == "__main__":
    main()