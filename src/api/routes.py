from typing import List, Union

from fastapi import APIRouter, Query  # type: ignore

# insights classes/runners
from insights.base import InsightResult
from insights.runner import generate_insights

# portfolio asset classes
from models.portfolio_assets import CryptoAsset, FiatAsset

# portfolio services
from services.portfolio import get_portfolio

router = APIRouter()


@router.get("/holdings", response_model=List[CryptoAsset])
async def fetch_holdings(
    staked_only: bool = Query(False, description="Only return staked assets")
):
    portfolio = await get_portfolio()
    if staked_only:
        portfolio = [asset for asset in portfolio if asset.is_staked]
    return portfolio


@router.get("/insights", response_model=List[InsightResult])
async def get_insights():
    # Step 1: Get enriched asset holdings
    holdings: List[Union[CryptoAsset, FiatAsset]] = await get_portfolio()

    # Step 2: Run insights (filter to crypto only)
    crypto_holdings = [a for a in holdings if isinstance(a, CryptoAsset)]
    insights = generate_insights(crypto_holdings)

    # Step 3: Return results
    return insights
