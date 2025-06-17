import os
from dotenv import load_dotenv # type: ignore
from coinbase import jwt_generator
import requests

load_dotenv()

class CoinbaseRequestHandler:
    def __init__(self):
        self.api_key = os.getenv("COINBASE_API_KEY")
        self.base_url = "https://api.coinbase.com"
        self.brokerage_accounts_api = "/api/v3/brokerage/accounts"
        self.key_path = os.getenv("COINBASE_API_SECRET_PATH")

    @property
    def api_secret(self) -> str:
        with open(self.key_path, 'r') as f:
            return f.read()

    def build_jwt_for(self, path: str, method: str = "GET") -> str:
        jwt_uri = jwt_generator.format_jwt_uri(method, path)
        return jwt_generator.build_rest_jwt(jwt_uri, self.api_key, self.api_secret)
    
    def get_holdings(self):

        headers = lambda token: {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            self.base_url + self.brokerage_accounts_api,
            headers=headers(self.build_jwt_for(self.brokerage_accounts_api))
        )

        if response.status_code != 200:
            raise Exception(f"Failed to fetch accounts: {response.status_code} {response.text}")

        accounts = response.json().get("accounts", [])
        portfolio = []

        for acct in accounts:
            balance = float(acct["available_balance"]["value"])
            if balance > 0:
                portfolio.append({
                    "symbol": acct["currency"],
                    "balance": balance,
                    "usd_value": balance
                })

        return portfolio