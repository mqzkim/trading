"""API 의존성 -- 인증, 의존성 주입."""
import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="x-api-key")


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    valid_key = os.getenv("COMMERCIAL_API_KEY", "dev-key-12345")
    if api_key != valid_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


def get_score_handler():
    from src.scoring.application import ScoreSymbolHandler
    from src.scoring.infrastructure import SqliteScoreRepository
    return ScoreSymbolHandler(score_repo=SqliteScoreRepository())


def get_regime_repo():
    from src.regime.infrastructure import SqliteRegimeRepository
    return SqliteRegimeRepository()
