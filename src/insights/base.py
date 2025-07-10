from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from pydantic import BaseModel  # type: ignore

from models.portfolio_assets import CryptoAsset, FiatAsset


class InsightResult(BaseModel):
    title: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None  # e.g., {"gain": "+12.3%", "coin": "ETH"}
    tags: Optional[List[str]] = None  # e.g., ["top_gainer", "volatile"]


class Insight(ABC):
    @abstractmethod
    def run(self, assets: List[CryptoAsset | FiatAsset]) -> Optional[InsightResult]:
        pass
