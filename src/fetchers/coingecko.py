import asyncio
import os
from typing import Dict, Optional

import httpx  # type: ignore


class CoinGeckoBaseModel:
    """ """

    def __init__(self):
        # vars - apis
        self.api_key = os.getenv("COINGECKO_API_KEY")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": f"{self.api_key}",
        }


class SymbolCache(CoinGeckoBaseModel):
    """ """

    def __init__(self):
        super().__init__()
        # cache dict implementation
        self.symbol_to_id: Dict[str, str] = {}
        # api vars
        # self.coins_api = "/coins/list"
        self.coins_market_api = "/coins/markets"

    async def initialize(self):
        await self.refresh()

    async def refresh(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url + self.coins_market_api,
                    headers=self.headers,
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": 250,
                        "page": 1,
                    },
                )

                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch list of coins + symbols: {response.status_code} {response.text}"
                    )

                for coin in response.json():
                    symbol = coin.get("symbol", "").lower()
                    coin_id = coin.get("id")
                    if symbol and coin_id and not symbol in self.symbol_to_id:
                        self.symbol_to_id[symbol] = coin_id

        except Exception as e:
            print(f"Failed to refresh cache with error: {e}")

    def get_id(self, symbol: str) -> Optional[str]:
        coin_id = self.symbol_to_id.get(symbol.lower())
        if not coin_id:
            print(f"[SymbolCache] Warning: No CoinGecko ID found for symbol '{symbol}'")
        return coin_id
