"""QuantScore API -- FastAPI app with JWT auth and tiered rate limiting."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .middleware.rate_limit import limiter
from .routers import auth

app = FastAPI(
    title="QuantScore API",
    description="Quantitative scoring and market regime data API. Not investment advice.",
    version="1.1.0",
)

# Rate limiter
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.1.0"}


# v1 API routes
app.include_router(auth.router, prefix="/api/v1")
