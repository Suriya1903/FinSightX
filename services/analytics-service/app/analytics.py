from sqlalchemy import text
from sqlalchemy.orm import Session


def get_overall_summary(db: Session) -> dict:
    """
    Return overall transaction KPIs from the analytical warehouse.
    """

    result = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS transaction_count,
                COALESCE(SUM(amount), 0) AS total_amount,
                COALESCE(AVG(amount), 0) AS average_transaction_amount,
                COUNT(DISTINCT customer_key) AS unique_customers,
                COUNT(DISTINCT merchant_key) AS unique_merchants,
                COUNT(DISTINCT device_key) AS unique_devices,
                COUNT(DISTINCT location_key) AS unique_locations
            FROM analytics.fact_transactions
            """
        )
    ).mappings().one()

    return {
        "transaction_count": int(result["transaction_count"]),
        "total_amount": float(result["total_amount"]),
        "average_transaction_amount": float(
            result["average_transaction_amount"]
        ),
        "unique_customers": int(result["unique_customers"]),
        "unique_merchants": int(result["unique_merchants"]),
        "unique_devices": int(result["unique_devices"]),
        "unique_locations": int(result["unique_locations"]),
    }


def get_daily_analytics(db: Session) -> list[dict]:
    """
    Return transaction activity grouped by date.
    """

    results = db.execute(
        text(
            """
            SELECT
                d.full_date,
                d.day_of_week_name,
                d.is_weekend,
                COUNT(f.transaction_key) AS transaction_count,
                COALESCE(SUM(f.amount), 0) AS total_amount,
                COALESCE(AVG(f.amount), 0) AS average_transaction_amount
            FROM analytics.fact_transactions f
            JOIN analytics.dim_date d
                ON f.date_key = d.date_key
            GROUP BY
                d.full_date,
                d.day_of_week_name,
                d.is_weekend
            ORDER BY d.full_date
            """
        )
    ).mappings().all()

    return [
        {
            "date": row["full_date"].isoformat(),
            "day_of_week": row["day_of_week_name"],
            "is_weekend": bool(row["is_weekend"]),
            "transaction_count": int(row["transaction_count"]),
            "total_amount": float(row["total_amount"]),
            "average_transaction_amount": float(
                row["average_transaction_amount"]
            ),
        }
        for row in results
    ]


def get_merchant_analytics(db: Session) -> list[dict]:
    """
    Return transaction analytics grouped by merchant.
    """

    results = db.execute(
        text(
            """
            SELECT
                m.merchant_name,
                m.merchant_category,
                COUNT(f.transaction_key) AS transaction_count,
                COALESCE(SUM(f.amount), 0) AS total_amount,
                COALESCE(AVG(f.amount), 0) AS average_transaction_amount,
                COUNT(DISTINCT f.customer_key) AS unique_customers
            FROM analytics.fact_transactions f
            JOIN analytics.dim_merchant m
                ON f.merchant_key = m.merchant_key
            GROUP BY
                m.merchant_name,
                m.merchant_category
            ORDER BY total_amount DESC
            """
        )
    ).mappings().all()

    return [
        {
            "merchant_name": row["merchant_name"],
            "merchant_category": row["merchant_category"],
            "transaction_count": int(row["transaction_count"]),
            "total_amount": float(row["total_amount"]),
            "average_transaction_amount": float(
                row["average_transaction_amount"]
            ),
            "unique_customers": int(row["unique_customers"]),
        }
        for row in results
    ]


def get_customer_analytics(db: Session) -> list[dict]:
    """
    Return transaction analytics grouped by customer.
    """

    results = db.execute(
        text(
            """
            SELECT
                c.customer_id,
                c.full_name,
                c.country,
                c.status,
                COUNT(f.transaction_key) AS transaction_count,
                COALESCE(SUM(f.amount), 0) AS total_amount,
                COALESCE(AVG(f.amount), 0) AS average_transaction_amount,
                COUNT(DISTINCT f.merchant_key) AS unique_merchants,
                COUNT(DISTINCT f.device_key) AS unique_devices
            FROM analytics.fact_transactions f
            JOIN analytics.dim_customer c
                ON f.customer_key = c.customer_key
            GROUP BY
                c.customer_id,
                c.full_name,
                c.country,
                c.status
            ORDER BY total_amount DESC
            """
        )
    ).mappings().all()

    return [
        {
            "customer_id": str(row["customer_id"]),
            "full_name": row["full_name"],
            "country": row["country"],
            "status": row["status"],
            "transaction_count": int(row["transaction_count"]),
            "total_amount": float(row["total_amount"]),
            "average_transaction_amount": float(
                row["average_transaction_amount"]
            ),
            "unique_merchants": int(row["unique_merchants"]),
            "unique_devices": int(row["unique_devices"]),
        }
        for row in results
    ]


def get_risk_analytics(db: Session) -> dict:
    """
    Return fraud/risk analytics from the warehouse.

    Risk values can be NULL for transactions whose fraud assessment
    has not yet been persisted into the analytical warehouse.
    """

    summary = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_transactions,
                COUNT(risk_level) AS assessed_transactions,
                COUNT(*) FILTER (
                    WHERE risk_level = 'HIGH'
                ) AS high_risk_transactions,
                COUNT(*) FILTER (
                    WHERE risk_level = 'MEDIUM'
                ) AS medium_risk_transactions,
                COUNT(*) FILTER (
                    WHERE risk_level = 'LOW'
                ) AS low_risk_transactions,
                COALESCE(
                    AVG(risk_score) FILTER (
                        WHERE risk_score IS NOT NULL
                    ),
                    0
                ) AS average_risk_score
            FROM analytics.fact_transactions
            """
        )
    ).mappings().one()

    by_risk = db.execute(
        text(
            """
            SELECT
                COALESCE(risk_level, 'NOT_ASSESSED') AS risk_level,
                COUNT(*) AS transaction_count,
                COALESCE(SUM(amount), 0) AS total_amount
            FROM analytics.fact_transactions
            GROUP BY COALESCE(risk_level, 'NOT_ASSESSED')
            ORDER BY transaction_count DESC
            """
        )
    ).mappings().all()

    return {
        "total_transactions": int(summary["total_transactions"]),
        "assessed_transactions": int(summary["assessed_transactions"]),
        "unassessed_transactions": (
            int(summary["total_transactions"])
            - int(summary["assessed_transactions"])
        ),
        "high_risk_transactions": int(
            summary["high_risk_transactions"]
        ),
        "medium_risk_transactions": int(
            summary["medium_risk_transactions"]
        ),
        "low_risk_transactions": int(
            summary["low_risk_transactions"]
        ),
        "average_risk_score": float(
            summary["average_risk_score"]
        ),
        "risk_breakdown": [
            {
                "risk_level": row["risk_level"],
                "transaction_count": int(row["transaction_count"]),
                "total_amount": float(row["total_amount"]),
            }
            for row in by_risk
        ],
    }