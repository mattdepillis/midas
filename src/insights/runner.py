from typing import List

from models.portfolio_assets import CryptoAsset, FiatAsset

from .base import InsightResult
from .top_movers import TopMoversInsight

INSIGHT_PLUGINS = [
    TopMoversInsight(),
    # Add more insights here later
]


def generate_insights(assets: List[CryptoAsset | FiatAsset]) -> List[InsightResult]:
    results = []
    for plugin in INSIGHT_PLUGINS:
        result = plugin.run(assets)
        if result:
            results.append(result)
    return results
