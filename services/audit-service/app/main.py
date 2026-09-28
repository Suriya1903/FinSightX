import logging

from fastapi import FastAPI
from sqlalchemy import text

from app.consumer import start_consumer_thread
from app.database import Base, engine
from app.models import AuditEvent


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


app = FastAPI(
    title="FinSightX Audit Service",
    description="Kafka-powered audit service for FinSightX.",
    version="0.1.0",
)


@app.on_event("startup")
async def startup() -> None:
    Base.metadata.create_all(
        bind=engine
    )

    start_consumer_thread()


@app.get("/")
async def root():
    return {
        "service": "audit-service",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        return {
            "service": "audit-service",
            "status": "healthy",
        }

    except Exception as exc:
        return {
            "service": "audit-service",
            "status": "unhealthy",
            "error": str(exc),
        }