import os
from typing import Dict, List, Optional

import httpx  # type: ignore


class CoinGeckoBaseModel:
    """
    Base class for shared CoinGecko configuration, including API key handling,
    base URL, and request headers.

    Attributes:
        api_key (str): API key loaded from environment variable.
        base_url (str): Base URL for the CoinGecko API.
        coins_market_api (str): Endpoint for querying market data.
        headers (Dict[str, str]): Common headers used for API requests.
        page_limit (int): Default pagination size for market requests.
    """

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
        self.number_pages = 3  # to start!


class CoinGeckoFetcher(CoinGeckoBaseModel):
    """
    Client for querying enriched market metadata (e.g., price changes, market cap)
    from CoinGecko's /coins/markets endpoint.

    Inherits:
        CoinGeckoBaseModel: For shared API config and headers.
    """

    def __init__(self):
        super().__init__()
        # api vars
        self.query_params = lambda coin_ids: {
            "vs_currency": "usd",
            "ids": coin_ids,
            "order": "market_cap_desc",
            "per_page": len(coin_ids),
            "page": 1,
            "price_change_percentage": "24h,7d,14d,30d,200d,1y",
        }

    async def get_price_metadata(self, ids: List[str]) -> Dict[str, float]:
        """
        Fetches enriched price and market metadata for a list of CoinGecko coin IDs.

        Args:
            ids (List[str]): A list of CoinGecko asset IDs (e.g., 'bitcoin', 'ethereum').

        Returns:
            Dict[str, Dict]: A mapping from coin ID to its market metadata.
        """
        try:
            id_str = ",".join(ids)

            async with httpx.AsyncClient() as client:
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


class MarketDataCache(CoinGeckoBaseModel):
    """
    In-memory cache for mapping asset symbols (e.g., 'btc') to CoinGecko IDs
    (e.g., 'bitcoin') using the /coins/list endpoint.

    Attributes:
        symbol_to_id (Dict[str, str]): Maps lowercase asset symbols to CoinGecko IDs.
    """

    def __init__(self, store_backend=None, market_store_backend=None):
        super().__init__()
        # cache dict implementation
        self.symbol_to_id: Dict[str, str] = store_backend or {}
        self.id_to_market_data: Dict[str, Dict] = market_store_backend or {}
        # api vars
        self.query_params = lambda page_num: {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": self.page_limit,
            "page": page_num,
            "price_change_percentage": "24h,7d,14d,30d,200d,1y",
        }

    async def initialize(self):
        """
        Initializes the symbol cache by calling refresh(). Intended to be used once at startup.
        """
        await self.refresh()

    async def refresh(self):
        """
        Calls the CoinGecko /coins/list endpoint and builds a symbol-to-ID mapping.
        Only symbols with both 'symbol' and 'id' fields are included.
        """
        try:
            async with httpx.AsyncClient() as client:
                # for now, limit coins to the top 500 by market cap
                for page in range(1, 4):
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
                            self.id_to_market_data[coin_id] = {**coin}

        except Exception as e:
            print(f"Failed to refresh cache with error: {e}")

    def get_id_from_symbol(self, symbol: str) -> Optional[str]:
        """
        Retrieves the CoinGecko ID for a given asset symbol.

        Args:
            symbol (str): Asset symbol (e.g., 'btc', 'eth').

        Returns:
            Optional[str]: Corresponding CoinGecko ID if found; otherwise None.
        """
        coin_id = self.symbol_to_id.get(symbol.lower())
        if not coin_id:
            print(f"[SymbolCache] Warning: No CoinGecko ID found for symbol '{symbol}'")
        return coin_id
