from typing import List

from fastapi import APIRouter, Query  # type: ignore

from models.portfolio import CoinbasePortfolioAsset
from services.portfolio import get_portfolio

router = APIRouter()


@router.get("/holdings", response_model=List[CoinbasePortfolioAsset])
async def fetch_holdings(
    staked_only: bool = Query(False, description="Only return staked assets")
):
    portfolio = await get_portfolio()
    if staked_only:
        portfolio = [asset for asset in portfolio if asset.is_staked]
    return portfolio
