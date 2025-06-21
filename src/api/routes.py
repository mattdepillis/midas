from typing import List

from fastapi import APIRouter  # type: ignore

from models.portfolio import CoinbasePortfolioAsset
from services.portfolio import get_portfolio

router = APIRouter()


@router.get("/holdings", response_model=List[CoinbasePortfolioAsset])
def fetch_holdings():
    return get_portfolio()
