"""Commercial API -- FastAPI application."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import score_router, regime_router, signal_router
from .models import HealthResponse

app = FastAPI(
    title="Trading System Commercial API",
    description="QuantScore | RegimeRadar | SignalFusion -- information only",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


app.include_router(score_router, tags=["QuantScore"])
app.include_router(regime_router, tags=["RegimeRadar"])
app.include_router(signal_router, tags=["SignalFusion"])
