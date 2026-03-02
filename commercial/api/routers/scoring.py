"""Scoring 라우터."""
from fastapi import APIRouter, Depends, HTTPException
from ..schemas import ScoreResponse, BatchScoreRequest, BatchScoreResponse, DISCLAIMER
from ..dependencies import verify_api_key, get_score_handler
from src.scoring.application import ScoreSymbolCommand
from src.shared.domain import Ok, Err

router = APIRouter(prefix="/v1/score", tags=["Scoring"])


@router.post("/{symbol}", response_model=ScoreResponse)
async def score_symbol(
    symbol: str,
    strategy: str = "swing",
    handler=Depends(get_score_handler),
    _=Depends(verify_api_key),
):
    result = handler.handle(ScoreSymbolCommand(symbol=symbol, strategy=strategy))
    if isinstance(result, Err):
        raise HTTPException(status_code=422, detail=str(result.error))
    data = result.value
    return ScoreResponse(**data, disclaimer=DISCLAIMER)


@router.get("/{symbol}/latest", response_model=ScoreResponse)
async def get_latest_score(
    symbol: str,
    _=Depends(verify_api_key),
):
    from src.scoring.infrastructure import SqliteScoreRepository
    repo = SqliteScoreRepository()
    score = repo.find_latest(symbol.upper())
    if score is None:
        raise HTTPException(status_code=404, detail=f"No cached score for {symbol}")
    return ScoreResponse(
        symbol=symbol.upper(),
        safety_passed=True,
        composite_score=score.value,
        risk_adjusted_score=score.risk_adjusted,
        strategy=score.strategy,
    )
