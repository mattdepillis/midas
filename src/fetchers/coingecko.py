import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import httpx  # type: ignore

from models.market_data import MarketData


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
        self.num_pages = 3  # to start!


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
        self.timeframes = ["7d", "14d", "30d", "200d", "1y"]
        self.query_params_specific_symbols = lambda symbols: {
            "vs_currency": "usd",
            "order": "market_cap_desc",  # to ensure that we grab the most relevant
            "symbols": symbols,
            "price_change_percentage": ",".join(self.timeframes),
        }
        self.query_params_top_assets = lambda page_num: {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": self.page_limit,
            "page": page_num,
            "price_change_percentage": ",".join(self.timeframes),
        }

    def _extract_clean_price_changes(self, coin: dict) -> dict:
        return {
            f"price_change_percentage_{t}": coin.get(
                f"price_change_percentage_{t}_in_currency"
            )
            for t in self.timeframes
        }

    async def get_top_assets(self) -> Tuple[Dict[str, str], Dict[str, dict]]:
        """
        Calls the CoinGecko /coins/list endpoint and builds a symbol-to-ID mapping.
        Only symbols with both 'symbol' and 'id' fields are included.
        """
        try:
            async with httpx.AsyncClient() as client:
                # for now, limit coins to the top 500 by market cap
                symbol_to_id = {}
                id_to_market_data = {}
                for page in range(1, 4):
                    response = await client.get(
                        self.base_url + self.coins_market_api,
                        headers=self.headers,
                        params=self.query_params_top_assets(page),
                    )

                    if response.status_code != 200:
                        raise Exception(
                            f"Failed to fetch list of coins + symbols: {response.status_code} {response.text}"
                        )

                    for coin in response.json():
                        symbol = coin.get("symbol", "").lower()
                        coin_id = coin.get("id")
                        if symbol and coin_id and symbol not in symbol_to_id:
                            symbol_to_id[symbol] = coin_id
                            cleaned_data = {
                                **coin,
                                **self._extract_clean_price_changes(coin),
                            }
                            id_to_market_data[coin_id] = MarketData(**cleaned_data)

            return (symbol_to_id, id_to_market_data)

        except Exception as e:
            print(
                f"Failed to fetch top {self.page_limit * self.num_pages} with error: {e}"
            )
            return ({}, {})

    async def get_coin_market_data_by_symbol(self, symbols: List[str]) -> bool:
        """ """
        try:
            async with httpx.AsyncClient() as client:
                # join symbols together in comma-separated string
                symbol_str = ",".join(symbols)
                response = await client.get(
                    self.base_url + self.coins_market_api,
                    headers=self.headers,
                    params=self.query_params_specific_symbols(symbol_str),
                )

                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch list of coins + symbols: {response.status_code} {response.text}"
                    )

                coin = response.json()[
                    0
                ]  # for now, assume this is only called for one coin at a time
                coin_id = coin.get("id")
                cleaned_data = {
                    **coin,
                    **self._extract_clean_price_changes(coin),
                }
                coin_market_data = MarketData(**cleaned_data)

                return coin_id, coin_market_data

        except Exception as e:
            print(
                f"Failed to fetch data for coins with symbols '{symbol_str}' with error: {e}"
            )
            return (None, {})


class MarketDataCache(CoinGeckoBaseModel):
    """
    In-memory cache for mapping asset symbols (e.g., 'btc') to CoinGecko IDs
    (e.g., 'bitcoin') using the /coins/list endpoint.

    Attributes:
        symbol_to_id (Dict[str, str]): Maps lowercase asset symbols to CoinGecko IDs.
    """

    def __init__(
        self, ttl_seconds: int = 3600, store_backend=None, market_store_backend=None
    ):
        super().__init__()
        # cache dict implementation
        self.symbol_to_id: Dict[str, str] = store_backend or {}
        self.id_to_market_data: Dict[str, MarketData] = market_store_backend or {}
        self._last_refreshed: Optional[datetime] = None
        self.ttl_seconds = ttl_seconds
        # external assets
        self._fetcher = CoinGeckoFetcher()

    async def initialize(self):
        """
        Initializes the symbol cache by calling refresh(). Intended to be used once at startup.
        """
        await self._refresh_cache()

    async def maybe_refresh(self):
        """ """
        if (
            self._last_refreshed is None
            or datetime.now() - self._last_refreshed
            > timedelta(seconds=self.ttl_seconds)
        ):
            await self._refresh_cache()

    async def _refresh_cache(self):
        print("[MarketDataCache] Refreshing cache...")
        (symbol_to_id, id_to_market_data) = await self._fetcher.get_top_assets()
        self.symbol_to_id = {**symbol_to_id}
        self.id_to_market_data = {**id_to_market_data}
        self._last_refreshed = datetime.now()

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

    async def get_asset_fallback(self, symbol: str) -> Optional[str]:
        """ """
        (asset_id, market_data) = await self._fetcher.get_coin_market_data_by_symbol(
            list(symbol)
        )
        if asset_id is not None:
            self.symbol_to_id[symbol] = asset_id
            self.id_to_market_data[asset_id] = market_data
            return asset_id
        print(f"Could not fetch market data for asset with symbol '{symbol}'.")
        return None
