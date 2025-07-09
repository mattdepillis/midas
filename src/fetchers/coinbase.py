import asyncio
import os
from typing import Any, Dict, List

import httpx  # type: ignore
from coinbase import jwt_generator


class CoinbaseRequestHandler:
    """
    Handles authenticated Coinbase API requests to fetch account balances and
    spot prices for crypto assets.

    Provides:
        - Authenticated access to the /accounts and /prices endpoints
        - Construction of a structured portfolio with enriched USD values
        - Support for staked assets and APY extraction

    Requires:
        - COINBASE_API_KEY (env var)
        - COINBASE_API_SECRET_PATH (path to secret for signing requests)
    """

    def __init__(self):
        # Authentication config
        self.api_key = os.getenv("COINBASE_API_KEY")
        self.key_path = os.getenv("COINBASE_API_SECRET_PATH")

        # API endpoints
        self.base_url = "https://api.coinbase.com"
        self.accounts_api = "/api/v2/accounts"
        self.assets_api = lambda symbol: f"/v2/prices/{symbol}-USD/spot"

        # Header constructor for authenticated requests
        self.headers = lambda token: {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @property
    def api_secret(self) -> str:
        """
        Reads the API secret from a file path defined in COINBASE_API_SECRET_PATH.

        Returns:
            The API secret as a string.
        """
        with open(self.key_path, "r") as f:
            return f.read()

    def build_jwt_for(self, path: str, method: str = "GET") -> str:
        """
        Generates a JWT token for a specific Coinbase API request.

        Args:
            path: The request path (e.g., "/api/v2/accounts").
            method: HTTP method (default "GET").

        Returns:
            A signed JWT string for authentication.
        """
        jwt_uri = jwt_generator.format_jwt_uri(method, path)
        return jwt_generator.build_rest_jwt(jwt_uri, self.api_key, self.api_secret)

    async def _get_all_accounts(self) -> List[Dict[str, Any]]:
        """
        Fetches all account records from the Coinbase v2 API.

        Returns:
            A list of account dictionaries.

        Raises:
            Exception if the API call fails.
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
        """
        Fetches the current USD spot price for a given crypto asset.

        Args:
            symbol: Asset symbol (e.g., "ETH", "BTC").

        Returns:
            The asset's USD spot price as a float, or 0.0 if unavailable.
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
        """
        Converts raw account records into a structured portfolio with price enrichment.

        Args:
            accounts: A list of account dicts from the Coinbase API.

        Returns:
            A sorted list of enriched asset dictionaries, descending by USD value.
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

    async def get_holdings(self) -> List[Dict[str, Any]]:
        """
        Public method to retrieve the user's full portfolio from Coinbase.

        Returns:
            A list of enriched asset holdings, each with:
              - id, name, symbol
              - balance and usd_price
              - usd_value
              - staking status and APY (if applicable)
        """
        accounts = await self._get_all_accounts()
        return await self._construct_portfolio(accounts)
