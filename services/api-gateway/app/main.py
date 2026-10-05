from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.cache import router as cache_router
from app.api.customers import router as customer_router
from app.api.database import router as database_router
from app.api.transactions import router as transaction_router
from app.metrics import record_http_request


app = FastAPI(
    title="FinSightX API Gateway",
    description=(
        "API Gateway for the FinSightX distributed "
        "financial intelligence platform."
    ),
    version="0.4.0",
)


@app.middleware("http")
async def prometheus_metrics_middleware(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_seconds = time.perf_counter() - start_time

    path = request.url.path

    record_http_request(
        method=request.method,
        path=path,
        status_code=response.status_code,
        duration_seconds=duration_seconds,
    )

    return response


app.include_router(database_router)
app.include_router(cache_router)
app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(transaction_router)
app.include_router(admin_router)


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        content={
            "service": "FinSightX API Gateway",
            "status": "running",
            "version": "0.4.0",
            "message": (
                "FinSightX API Gateway is running successfully."
            ),
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


@app.get("/metrics")
async def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )