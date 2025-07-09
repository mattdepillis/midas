import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import httpx  # type: ignore


class FiatRateCache:
    """
    Caches fiat-to-USD exchange rates using Frankfurter.app.
    Used to convert fiat currency balances (e.g., JPY, EUR) to USD values
    for portfolio enrichment.

    Rates are cached in memory and refreshed periodically based on TTL.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initializes the cache instance.

        Args:
            ttl_seconds: Time-to-live for the cached exchange rates, in seconds.
                         After this duration, the cache will be refreshed automatically.
        """
        self.base_url = f"https://api.frankfurter.app"
        self.usd_rates_api = (
            "/latest?to=USD"  # Endpoint returns rates with USD as the target currency
        )
        self.rates: Dict[str, float] = (
            {}
        )  # Maps lowercase currency symbols (e.g., 'eur') to float USD rates
        self._last_refreshed: Optional[datetime] = None
        self.ttl_seconds = ttl_seconds

    async def initialize(self) -> None:
        """
        Loads exchange rates into the cache at startup.
        Intended to be called once on application init.
        """
        await self._refresh_cache()

    async def _refresh_cache(self) -> None:
        """
        Fetches fresh exchange rates from the Frankfurter API
        and updates the internal cache.

        Adds 'usd' manually to ensure consistent behavior for USD balances.
        """
        async with httpx.AsyncClient() as client:
            print("[FiatRateCache] Refreshing cache...")
            resp = await client.get(self.base_url + self.usd_rates_api)
            data = resp.json()
            self.rates = {k.lower(): float(v) for k, v in data["rates"].items()}
            self.rates["usd"] = 1.0  # Ensure USD is handled
            self._last_refreshed = datetime.now()

    async def maybe_refresh(self) -> None:
        """
        Checks if the cache has expired based on the TTL.
        If so, triggers a refresh.
        """
        if (
            self._last_refreshed is None
            or datetime.now() - self._last_refreshed
            > timedelta(seconds=self.ttl_seconds)
        ):
            await self._refresh_cache()

    def get_rate(self, symbol: str) -> Optional[float]:
        """
        Retrieves the cached USD conversion rate for a given fiat currency symbol.

        Args:
            symbol: The fiat currency symbol (e.g., "eur", "jpy", "usd").

        Returns:
            The USD conversion rate, or None if not found.
        """
        return self.rates.get(symbol.lower())
