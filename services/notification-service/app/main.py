import logging
import threading

from fastapi import FastAPI

from app.consumer import consume_events


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("finsightx-notification")


app = FastAPI(
    title="FinSightX Notification Service",
    description="Kafka-powered notification service for FinSightX.",
    version="0.1.0",
)


@app.on_event("startup")
async def startup() -> None:
    logger.info(
        "Starting FinSightX Notification Service..."
    )

    consumer_thread = threading.Thread(
        target=consume_events,
        daemon=True,
        name="notification-kafka-consumer",
    )

    consumer_thread.start()

    logger.info(
        "Notification Kafka consumer thread started."
    )


@app.get("/")
async def root():
    return {
        "service": "notification-service",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    return {
        "service": "notification-service",
        "status": "healthy",
    }


@app.get("/ready")
async def ready():
    return {
        "service": "notification-service",
        "status": "ready",
        "kafka_topic": "fraud.assessed",
        "kafka_group": "finsightx-notification-service",
    }