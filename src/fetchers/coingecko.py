import asyncio
import os
from typing import Dict, List, Optional

import httpx  # type: ignore


class CoinGeckoBaseModel:
    """ """

    def __init__(self):
        # vars - apis
        self.api_key = os.getenv("COINGECKO_API_KEY")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.coins_market_api = "/coins/markets"
        self.headers = {
            "accept": "application/json",
            "x-cg-demo-api-key": f"{self.api_key}",
        }
        self.page_limit = 250  # to start!


class CoinGeckoFetcher(CoinGeckoBaseModel):
    """ """

    def __init__(self):
        super().__init__()
        # api vars
        self.query_params = lambda coin_ids: {
            "vs_currency": "usd",
            "ids": coin_ids,
            "order": "market_cap_desc",
            "per_page": len(coin_ids),
            "page": 1,
            "price_change_percentage": "24h,7d,14d",
        }

    async def get_price_metadata(self, ids: List[str]) -> Dict[str, float]:
        """ """
        try:
            id_str = ",".join(ids)

            async with httpx.AsyncClient() as client:
                print("s", self.headers)
                response = await client.get(
                    self.base_url + self.coins_market_api,
                    headers=self.headers,
                    params=self.query_params(id_str),
                )
                data = response.json()
                return {item["id"]: {**item} for item in data if "id" in item}
        except Exception as e:
            print(f"Could not retrieve prices for ids via CoinGecko due to error: {e}")
            return {}  # return empty dict if exception encountered


class SymbolCache(CoinGeckoBaseModel):
    """ """

    def __init__(self):
        super().__init__()
        # cache dict implementation
        self.symbol_to_id: Dict[str, str] = {}
        # api vars
        self.query_params = lambda page_num: {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": self.page_limit,
            "page": page_num,
        }

    async def initialize(self):
        """ """
        await self.refresh()

    async def refresh(self):
        """ """
        try:
            async with httpx.AsyncClient() as client:
                # for now, limit coins to the top 500 by market cap
                for page in range(1, 5):
                    response = await client.get(
                        self.base_url + self.coins_market_api,
                        headers=self.headers,
                        params=self.query_params(page),
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
        """ """
        coin_id = self.symbol_to_id.get(symbol.lower())
        if not coin_id:
            print(f"[SymbolCache] Warning: No CoinGecko ID found for symbol '{symbol}'")
        return coin_id
