from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Query
from sqlalchemy import desc, select

from app.config import settings
from app.consumer import audit_consumer
from app.database import Base, SessionLocal, engine
from app.models import AuditLog
from app.schemas import AuditLogResponse
from app.security import require_admin


@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(
        bind=engine
    )

    audit_consumer.start()

    yield

    audit_consumer.stop()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Event-driven audit service for FinSightX."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "service": "audit-service",
        "status": "healthy",
    }


@app.get("/ready")
async def ready():
    return {
        "service": "audit-service",
        "status": "ready",
        "kafka_topic": settings.KAFKA_TOPIC,
    }


@app.get("/api/v1/audit", response_model=list[AuditLogResponse])
async def list_audit_logs(
    _admin_user: Annotated[
        dict,
        Depends(require_admin),
    ],
    limit: int = Query(
        default=50,
        ge=1,
        le=500,
    ),
):

    with SessionLocal() as db:

        statement = (
            select(AuditLog)
            .order_by(
                desc(AuditLog.occurred_at)
            )
            .limit(limit)
        )

        records = db.scalars(
            statement
        ).all()

        return list(records)