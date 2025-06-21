from fetchers.coinbase import CoinbaseRequestHandler


def get_portfolio():
    client = CoinbaseRequestHandler()
    return client.get_holdings()
