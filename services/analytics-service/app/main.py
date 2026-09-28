from fastapi import FastAPI, HTTPException

from app.analytics import (
    get_customer_analytics,
    get_daily_analytics,
    get_merchant_analytics,
    get_overall_summary,
    get_risk_analytics,
)
from app.database import get_db
from app.etl import run_etl, run_lake_etl


app = FastAPI(
    title="FinSightX Analytics Service",
    description=(
        "Analytics and data warehouse ETL service for "
        "FinSightX."
    ),
    version="1.2.0",
)


# ==========================================================
# BASIC ENDPOINTS
# ==========================================================

@app.get("/")
async def root():
    return {
        "service": "FinSightX Analytics Service",
        "status": "running",
        "version": "1.2.0",
    }


@app.get("/health")
async def health():
    return {
        "service": "analytics-service",
        "status": "healthy",
    }


# ==========================================================
# ORIGINAL OPERATIONAL ETL
# ==========================================================

@app.post("/api/v1/etl/run")
def execute_etl():
    """
    Run the original operational database → warehouse ETL.
    """

    db = get_db()

    try:
        result = run_etl(db)

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"ETL pipeline failed: {exc}",
        )

    finally:
        db.close()


# ==========================================================
# NEW LAKE → WAREHOUSE ETL
# ==========================================================

@app.post("/api/v1/etl/lake/run")
def execute_lake_etl():
    """
    Run the processed data lake → staging → warehouse ETL.

    Flow:

        MinIO processed data
                ↓
        stg_processed_transactions
                ↓
        Warehouse dimensions
                ↓
        fact_transactions
    """

    db = get_db()

    try:
        result = run_lake_etl(db)

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Lake ETL pipeline failed: {exc}",
        )

    finally:
        db.close()


# ==========================================================
# ANALYTICS
# ==========================================================

@app.get("/api/v1/analytics/summary")
def analytics_summary():
    db = get_db()

    try:
        return get_overall_summary(db)

    finally:
        db.close()


@app.get("/api/v1/analytics/daily")
def analytics_daily():
    db = get_db()

    try:
        return {
            "data": get_daily_analytics(db)
        }

    finally:
        db.close()


@app.get("/api/v1/analytics/merchants")
def analytics_merchants():
    db = get_db()

    try:
        return {
            "data": get_merchant_analytics(db)
        }

    finally:
        db.close()


@app.get("/api/v1/analytics/customers")
def analytics_customers():
    db = get_db()

    try:
        return {
            "data": get_customer_analytics(db)
        }

    finally:
        db.close()


@app.get("/api/v1/analytics/risk")
def analytics_risk():
    db = get_db()

    try:
        return get_risk_analytics(db)

    finally:
        db.close()
