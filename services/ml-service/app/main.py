from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.model import FraudModel
from app.schemas import (
    FraudPredictionRequest,
    FraudPredictionResponse,
)


fraud_model = FraudModel()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.
    """

    fraud_model.load()

    yield


app = FastAPI(
    title="FinSightX ML Service",
    description=(
        "Machine learning inference service "
        "for real-time fraud detection."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    """
    Basic service health check.
    """

    return {
        "status": "healthy",
        "service": "ml-service",
    }


@app.get("/ready")
def ready() -> dict:
    """
    Readiness check.

    The service is ready only after the fraud model
    has been loaded successfully.
    """

    if fraud_model.model is None:
        raise HTTPException(
            status_code=503,
            detail="Fraud model is not loaded.",
        )

    return {
        "status": "ready",
        "service": "ml-service",
        "model_name": "fraud_random_forest",
        "model_version": fraud_model.model_version,
    }


@app.get("/")
def root() -> dict:
    """
    Service information endpoint.
    """

    return {
        "service": "FinSightX ML Service",
        "status": "running",
        "model": "fraud_random_forest",
        "model_version": fraud_model.model_version,
    }


@app.post(
    "/api/v1/predict",
    response_model=FraudPredictionResponse,
)
def predict(
    request: FraudPredictionRequest,
) -> FraudPredictionResponse:
    """
    Run fraud prediction for a transaction.
    """

    try:
        result = fraud_model.predict(
            request.model_dump()
        )

        return FraudPredictionResponse(
            **result
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {exc}",
        ) from exc