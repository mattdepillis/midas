from typing import List, Optional

from models.portfolio_assets import CryptoAsset, FiatAsset  # adjust path if needed

from .base import Insight, InsightResult


class TopMoversInsight(Insight):
    def run(self, assets: List[CryptoAsset | FiatAsset]) -> Optional[InsightResult]:
        # Only include assets with valid 24h change data
        assets_with_change = [
            a for a in assets if a.price_change_percentage_24h is not None
        ]

        if not assets_with_change:
            return None  # No applicable insight

        best_performers = self._get_top_n(
            assets_with_change, key="price_change_percentage_24h", reverse=True
        )
        worst_performers = self._get_top_n(
            assets_with_change, key="price_change_percentage_24h", reverse=False
        )

        metadata = {}

        for i, asset in enumerate(best_performers, 1):
            metadata[f"Best Performer {i}"] = (
                f"{asset.symbol} (+{asset.price_change_percentage_24h:.2f}%)"
            )

        for i, asset in enumerate(worst_performers, 1):
            metadata[f"Worst Performer {i}"] = (
                f"{asset.symbol} ({asset.price_change_percentage_24h:.2f}%)"
            )

        return InsightResult(
            title="Best/Worst Performers (24h)",
            description="Assets with the biggest % price changes in your portfolio over the last 24 hours.",
            metadata=metadata,
            tags=["volatility", "momentum"],
        )

    def _get_top_n(
        self, assets: List[CryptoAsset | FiatAsset], key: str, reverse: bool, n: int = 3
    ) -> List[CryptoAsset | FiatAsset]:
        return sorted(assets, key=lambda a: getattr(a, key, 0), reverse=reverse)[:n]
