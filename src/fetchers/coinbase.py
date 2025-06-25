import asyncio
import os
from typing import Any, Dict, List

import httpx  # type: ignore
from coinbase import jwt_generator

from models.portfolio import CryptoAsset


class CoinbaseRequestHandler:
    """Handles authenticated Coinbase API requests to fetch account balances and asset prices."""

    def __init__(self):
        # vars - secrets
        self.api_key = os.getenv("COINBASE_API_KEY")
        self.key_path = os.getenv("COINBASE_API_SECRET_PATH")
        # vars - apis
        self.base_url = "https://api.coinbase.com"
        self.accounts_api = "/api/v2/accounts"
        self.assets_api = lambda symbol: f"/v2/prices/{symbol}-USD/spot"
        # vars - headers
        self.headers = lambda token: {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @property
    def api_secret(self) -> str:
        with open(self.key_path, "r") as f:
            return f.read()

    def build_jwt_for(self, path: str, method: str = "GET") -> str:
        """Generates a JWT token for a specific API path and HTTP method.

        Args:
            path: The API endpoint path.
            method: The HTTP method (default is "GET").

        Returns:
            A signed JWT string for request authentication.
        """
        jwt_uri = jwt_generator.format_jwt_uri(method, path)
        return jwt_generator.build_rest_jwt(jwt_uri, self.api_key, self.api_secret)

    async def _get_all_accounts(self) -> List[Dict[str, Any]]:
        """Fetches all account records asynchronously from Coinbase v2 API.

        Returns:
            A list of account dictionaries from the /v2/accounts endpoint.

        Raises:
            Exception: If the API call fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url + self.accounts_api,
                headers=self.headers(self.build_jwt_for(self.accounts_api)),
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch accounts: {response.status_code} {response.text}"
                )

            return response.json().get("data", [])

    async def get_asset_price(self, symbol: str) -> float:
        """Fetches the current USD spot price for a given asset symbol.

        Args:
            symbol: The crypto asset symbol (e.g., 'SOL').

        Returns:
            The spot price as a float. Returns 0.0 on failure.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    self.base_url + self.assets_api(symbol),
                    headers=self.headers(self.build_jwt_for(self.assets_api(symbol))),
                )
                return float(response.json()["data"]["amount"])
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            print(f"Could not extract price for {symbol}")
            return 0.0

    async def _construct_portfolio(
        self, accounts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transforms raw account data into a structured portfolio with price info.

        Args:
            accounts: A list of raw account records from the API.

        Returns:
            A list of dictionaries, each representing a portfolio asset.
        """

        async def process_account(acct):
            balance = float(acct["balance"]["amount"])
            symbol = acct["currency"]["code"]
            if balance == 0:
                return None

            price = await self.get_asset_price(symbol)
            is_staked = acct["name"].lower().startswith("staked")
            return {
                "id": acct["id"],
                "name": acct["currency"]["name"],
                "symbol": symbol,
                "balance": balance,
                "usd_price": price,
                "usd_value": balance * price,
                "is_staked": is_staked,
                "apy": (
                    float(acct["currency"].get("rewards", {}).get("apy", 0))
                    if is_staked
                    else None
                ),
            }

        results = await asyncio.gather(*(process_account(acct) for acct in accounts))
        return sorted(
            [r for r in results if r], key=lambda x: x["usd_value"], reverse=True
        )

    async def get_holdings(self) -> List[CryptoAsset]:
        """Main public method to fetch and format portfolio holdings.

        Returns:
            A list of enriched holdings, including USD values and staking status.
        """
        accounts = await self._get_all_accounts()
        raw_assets = await self._construct_portfolio(accounts)
        return [CryptoAsset(**asset) for asset in raw_assets]
