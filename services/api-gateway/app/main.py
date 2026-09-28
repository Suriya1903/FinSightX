from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.cache import router as cache_router
from app.api.customers import router as customer_router
from app.api.database import router as database_router
from app.api.transactions import router as transaction_router


app = FastAPI(
    title="FinSightX API Gateway",
    description="API Gateway for the FinSightX distributed financial intelligence platform.",
    version="0.1.0",
)


app.include_router(database_router)
app.include_router(cache_router)
app.include_router(customer_router)
app.include_router(transaction_router)


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        content={
            "service": "FinSightX API Gateway",
            "status": "running",
            "version": "0.1.0",
            "message": "FinSightX API Gateway is running successfully.",
        }
    )


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(
        content={
            "service": "api-gateway",
            "status": "healthy",
        }
    )


@app.get("/api/v1")
async def api_version() -> JSONResponse:
    return JSONResponse(
        content={
            "api": "FinSightX",
            "version": "v1",
            "status": "available",
        }
    )