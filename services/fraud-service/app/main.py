import logging
import threading

from fastapi import FastAPI
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.consumer import consume_events
from app.database import ensure_ml_columns


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)


app = FastAPI(
    title="FinSightX Fraud Detection Service",
    description=(
        "Real-time rule-based and machine-learning "
        "fraud detection service for FinSightX."
    ),
    version="0.4.0",
)


@app.on_event("startup")
async def startup() -> None:

    ensure_ml_columns()

    consumer_thread = threading.Thread(
        target=consume_events,
        daemon=True,
        name="fraud-kafka-consumer",
    )

    consumer_thread.start()


@app.get("/")
async def root():
    return {
        "service": "fraud-service",
        "status": "running",
        "version": "0.4.0",
        "capabilities": [
            "rule-based-fraud-detection",
            "redis-velocity",
            "ml-fraud-prediction",
            "kafka-event-processing",
            "prometheus-metrics",
        ],
    }


@app.get("/health")
async def health():
    return {
        "service": "fraud-service",
        "status": "healthy",
    }


@app.get("/metrics")
async def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )