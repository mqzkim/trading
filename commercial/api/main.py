"""QuantScore API -- FastAPI 앱."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import score_router, regime_router, signal_router
from .routers import scoring as scoring_v1
from .routers import regime as regime_v1
from .models import HealthResponse

app = FastAPI(
    title="QuantScore API",
    description="정량적 스코어링 및 시장 레짐 데이터 API. 투자 자문 아님.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


# Legacy routes (core/ 기반)
app.include_router(score_router, tags=["QuantScore"])
app.include_router(regime_router, tags=["RegimeRadar"])
app.include_router(signal_router, tags=["SignalFusion"])

# v1 routes (src/ DDD 기반)
app.include_router(scoring_v1.router)
app.include_router(regime_v1.router)
