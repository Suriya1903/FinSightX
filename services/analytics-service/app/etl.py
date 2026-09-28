import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


logger = logging.getLogger("finsightx-analytics-etl")


# ==========================================================
# DATE DIMENSION
# ==========================================================

def load_date_dimension(
    db: Session,
    transaction_created_at: datetime,
) -> int:
    """
    Insert the transaction date into dim_date if it does not
    already exist and return the corresponding date_key.
    """

    transaction_date = transaction_created_at.date()

    date_key = int(
        transaction_date.strftime("%Y%m%d")
    )

    db.execute(
        text(
            """
            INSERT INTO analytics.dim_date (
                date_key,
                full_date,
                day_number,
                month_number,
                month_name,
                quarter_number,
                year_number,
                day_of_week_number,
                day_of_week_name,
                is_weekend
            )
            VALUES (
                :date_key,
                :full_date,
                :day_number,
                :month_number,
                :month_name,
                :quarter_number,
                :year_number,
                :day_of_week_number,
                :day_of_week_name,
                :is_weekend
            )
            ON CONFLICT (date_key)
            DO NOTHING
            """
        ),
        {
            "date_key": date_key,
            "full_date": transaction_date,
            "day_number": transaction_date.day,
            "month_number": transaction_date.month,
            "month_name": transaction_date.strftime("%B"),
            "quarter_number": (
                (transaction_date.month - 1) // 3
            ) + 1,
            "year_number": transaction_date.year,
            "day_of_week_number": transaction_date.isoweekday(),
            "day_of_week_name": transaction_date.strftime(
                "%A"
            ),
            "is_weekend": transaction_date.weekday() >= 5,
        },
    )

    return date_key


# ==========================================================
# CUSTOMER DIMENSION
# ==========================================================

def load_customer_dimension(
    db: Session,
    customer_id,
) -> int:
    """
    Load a customer into dim_customer and return customer_key.
    """

    customer = db.execute(
        text(
            """
            SELECT
                id,
                full_name,
                email,
                country,
                status,
                created_at,
                updated_at
            FROM customers
            WHERE id = :customer_id
            """
        ),
        {
            "customer_id": customer_id
        },
    ).mappings().one()

    db.execute(
        text(
            """
            INSERT INTO analytics.dim_customer (
                customer_id,
                full_name,
                email,
                country,
                status,
                source_created_at,
                source_updated_at
            )
            VALUES (
                :customer_id,
                :full_name,
                :email,
                :country,
                :status,
                :source_created_at,
                :source_updated_at
            )
            ON CONFLICT (customer_id)
            DO UPDATE SET
                full_name = EXCLUDED.full_name,
                email = EXCLUDED.email,
                country = EXCLUDED.country,
                status = EXCLUDED.status,
                source_created_at = EXCLUDED.source_created_at,
                source_updated_at = EXCLUDED.source_updated_at
            """
        ),
        {
            "customer_id": customer["id"],
            "full_name": customer["full_name"],
            "email": customer["email"],
            "country": customer["country"],
            "status": customer["status"],
            "source_created_at": customer["created_at"],
            "source_updated_at": customer["updated_at"],
        },
    )

    customer_key = db.execute(
        text(
            """
            SELECT customer_key
            FROM analytics.dim_customer
            WHERE customer_id = :customer_id
            """
        ),
        {
            "customer_id": customer_id
        },
    ).scalar_one()

    return int(customer_key)


# ==========================================================
# MERCHANT DIMENSION
# ==========================================================

def load_merchant_dimension(
    db: Session,
    merchant_name: str,
    merchant_category: str | None,
) -> int:
    """
    Load a merchant into dim_merchant and return merchant_key.
    """

    db.execute(
        text(
            """
            INSERT INTO analytics.dim_merchant (
                merchant_name,
                merchant_category
            )
            VALUES (
                :merchant_name,
                :merchant_category
            )
            ON CONFLICT (
                merchant_name,
                merchant_category
            )
            DO NOTHING
            """
        ),
        {
            "merchant_name": merchant_name,
            "merchant_category": merchant_category,
        },
    )

    merchant_key = db.execute(
        text(
            """
            SELECT merchant_key
            FROM analytics.dim_merchant
            WHERE merchant_name = :merchant_name
              AND merchant_category IS NOT DISTINCT FROM :merchant_category
            """
        ),
        {
            "merchant_name": merchant_name,
            "merchant_category": merchant_category,
        },
    ).scalar_one()

    return int(merchant_key)


# ==========================================================
# DEVICE DIMENSION
# ==========================================================

def load_device_dimension(
    db: Session,
    device_id: str | None,
) -> int | None:
    """
    Load a device into dim_device and return device_key.
    """

    if not device_id:
        return None

    db.execute(
        text(
            """
            INSERT INTO analytics.dim_device (
                device_id
            )
            VALUES (
                :device_id
            )
            ON CONFLICT (device_id)
            DO NOTHING
            """
        ),
        {
            "device_id": device_id
        },
    )

    device_key = db.execute(
        text(
            """
            SELECT device_key
            FROM analytics.dim_device
            WHERE device_id = :device_id
            """
        ),
        {
            "device_id": device_id
        },
    ).scalar_one()

    return int(device_key)


# ==========================================================
# LOCATION DIMENSION
# ==========================================================

def load_location_dimension(
    db: Session,
    location_name: str | None,
) -> int | None:
    """
    Load a location into dim_location and return location_key.
    """

    if not location_name:
        return None

    db.execute(
        text(
            """
            INSERT INTO analytics.dim_location (
                location_name
            )
            VALUES (
                :location_name
            )
            ON CONFLICT (location_name)
            DO NOTHING
            """
        ),
        {
            "location_name": location_name
        },
    )

    location_key = db.execute(
        text(
            """
            SELECT location_key
            FROM analytics.dim_location
            WHERE location_name = :location_name
            """
        ),
        {
            "location_name": location_name
        },
    ).scalar_one()

    return int(location_key)


# ==========================================================
# FACT TRANSACTION
# ==========================================================

def load_fact_transaction(
    db: Session,
    transaction,
) -> None:
    """
    Load or update one transaction in fact_transactions.

    Fraud information is retrieved from fraud_assessments.

    Existing fact rows are updated so that a fraud assessment
    created after the original ETL run is also reflected in
    the warehouse.
    """

    transaction_id = transaction["id"]

    # ------------------------------------------------------
    # Find latest fraud assessment
    # ------------------------------------------------------

    fraud_assessment = db.execute(
        text(
            """
            SELECT
                risk_level,
                risk_score
            FROM fraud_assessments
            WHERE transaction_id = :transaction_id
            ORDER BY assessed_at DESC
            LIMIT 1
            """
        ),
        {
            "transaction_id": transaction_id
        },
    ).mappings().first()

    risk_level = None
    risk_score = None

    if fraud_assessment:
        risk_level = fraud_assessment["risk_level"]
        risk_score = fraud_assessment["risk_score"]

    # ------------------------------------------------------
    # Load dimensions
    # ------------------------------------------------------

    date_key = load_date_dimension(
        db,
        transaction["created_at"],
    )

    customer_key = load_customer_dimension(
        db,
        transaction["customer_id"],
    )

    merchant_key = load_merchant_dimension(
        db,
        transaction["merchant_name"],
        transaction["merchant_category"],
    )

    device_key = load_device_dimension(
        db,
        transaction["device_id"],
    )

    location_key = load_location_dimension(
        db,
        transaction["location"],
    )

    # ------------------------------------------------------
    # Insert or update fact transaction
    # ------------------------------------------------------

    db.execute(
        text(
            """
            INSERT INTO analytics.fact_transactions (
                transaction_id,
                date_key,
                customer_key,
                merchant_key,
                device_key,
                location_key,
                amount,
                currency,
                transaction_status,
                risk_level,
                risk_score,
                transaction_created_at
            )
            VALUES (
                :transaction_id,
                :date_key,
                :customer_key,
                :merchant_key,
                :device_key,
                :location_key,
                :amount,
                :currency,
                :transaction_status,
                :risk_level,
                :risk_score,
                :transaction_created_at
            )
            ON CONFLICT (transaction_id)
            DO UPDATE SET
                date_key = EXCLUDED.date_key,
                customer_key = EXCLUDED.customer_key,
                merchant_key = EXCLUDED.merchant_key,
                device_key = EXCLUDED.device_key,
                location_key = EXCLUDED.location_key,
                amount = EXCLUDED.amount,
                currency = EXCLUDED.currency,
                transaction_status = EXCLUDED.transaction_status,
                risk_level = EXCLUDED.risk_level,
                risk_score = EXCLUDED.risk_score,
                transaction_created_at = EXCLUDED.transaction_created_at
            """
        ),
        {
            "transaction_id": transaction["id"],
            "date_key": date_key,
            "customer_key": customer_key,
            "merchant_key": merchant_key,
            "device_key": device_key,
            "location_key": location_key,
            "amount": transaction["amount"],
            "currency": transaction["currency"],
            "transaction_status": transaction["status"],
            "risk_level": risk_level,
            "risk_score": risk_score,
            "transaction_created_at": transaction["created_at"],
        },
    )


# ==========================================================
# ORIGINAL OPERATIONAL ETL
# ==========================================================

def run_etl(db: Session) -> dict:
    """
    Run the original transaction-to-warehouse ETL pipeline.

    Source:
        customers
        transactions
        fraud_assessments

    Destination:
        analytics dimensions
        analytics.fact_transactions
        analytics.etl_metadata
    """

    pipeline_name = "transaction_warehouse_etl"

    started_at = datetime.now(
        timezone.utc
    )

    records_processed = 0

    try:
        # --------------------------------------------------
        # Read all source transactions
        # --------------------------------------------------

        transactions = db.execute(
            text(
                """
                SELECT
                    id,
                    customer_id,
                    amount,
                    currency,
                    merchant_name,
                    merchant_category,
                    location,
                    device_id,
                    status,
                    created_at
                FROM transactions
                ORDER BY created_at
                """
            )
        ).mappings().all()

        logger.info(
            "ETL STARTED | source_transactions=%s",
            len(transactions),
        )

        # --------------------------------------------------
        # Load every transaction
        # --------------------------------------------------

        for transaction in transactions:
            load_fact_transaction(
                db,
                transaction,
            )

            records_processed += 1

        # --------------------------------------------------
        # Determine last processed timestamp
        # --------------------------------------------------

        last_processed_timestamp = None

        if transactions:
            last_processed_timestamp = transactions[-1][
                "created_at"
            ]

        # --------------------------------------------------
        # Update ETL metadata
        # --------------------------------------------------

        db.execute(
            text(
                """
                INSERT INTO analytics.etl_metadata (
                    pipeline_name,
                    last_processed_timestamp,
                    last_run_timestamp,
                    records_processed,
                    pipeline_status,
                    error_message
                )
                VALUES (
                    :pipeline_name,
                    :last_processed_timestamp,
                    :last_run_timestamp,
                    :records_processed,
                    :pipeline_status,
                    NULL
                )
                ON CONFLICT (pipeline_name)
                DO UPDATE SET
                    last_processed_timestamp =
                        EXCLUDED.last_processed_timestamp,
                    last_run_timestamp =
                        EXCLUDED.last_run_timestamp,
                    records_processed =
                        EXCLUDED.records_processed,
                    pipeline_status =
                        EXCLUDED.pipeline_status,
                    error_message = NULL
                """
            ),
            {
                "pipeline_name": pipeline_name,
                "last_processed_timestamp":
                    last_processed_timestamp,
                "last_run_timestamp": started_at,
                "records_processed": records_processed,
                "pipeline_status": "SUCCESS",
            },
        )

        db.commit()

        logger.info(
            "ETL COMPLETED | records_processed=%s",
            records_processed,
        )

        return {
            "pipeline": pipeline_name,
            "status": "SUCCESS",
            "records_processed": records_processed,
            "last_processed_timestamp": (
                last_processed_timestamp.isoformat()
                if last_processed_timestamp
                else None
            ),
            "completed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    except Exception as exc:

        db.rollback()

        logger.exception(
            "ETL FAILED"
        )

        db.execute(
            text(
                """
                INSERT INTO analytics.etl_metadata (
                    pipeline_name,
                    last_run_timestamp,
                    records_processed,
                    pipeline_status,
                    error_message
                )
                VALUES (
                    :pipeline_name,
                    :last_run_timestamp,
                    :records_processed,
                    :pipeline_status,
                    :error_message
                )
                ON CONFLICT (pipeline_name)
                DO UPDATE SET
                    last_run_timestamp =
                        EXCLUDED.last_run_timestamp,
                    records_processed =
                        EXCLUDED.records_processed,
                    pipeline_status =
                        EXCLUDED.pipeline_status,
                    error_message =
                        EXCLUDED.error_message
                """
            ),
            {
                "pipeline_name": pipeline_name,
                "last_run_timestamp": started_at,
                "records_processed": records_processed,
                "pipeline_status": "FAILED",
                "error_message": str(exc),
            },
        )

        db.commit()

        raise


# ==========================================================
# PROCESSED LAKE → WAREHOUSE ETL
# ==========================================================

def run_lake_etl(db: Session) -> dict:
    """
    Load processed transactions from the Spark staging table
    into the analytics warehouse.

    Source:
        analytics.stg_processed_transactions

    Enrichment:
        transactions
        customers
        fraud_assessments

    Destination:
        analytics.dim_date
        analytics.dim_customer
        analytics.dim_merchant
        analytics.dim_device
        analytics.dim_location
        analytics.fact_transactions
        analytics.etl_metadata
    """

    pipeline_name = "processed_lake_warehouse_etl"

    started_at = datetime.now(
        timezone.utc
    )

    records_processed = 0

    try:
        # --------------------------------------------------
        # Check staging table
        # --------------------------------------------------

        staging_count = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM analytics.stg_processed_transactions
                """
            )
        ).scalar_one()

        logger.info(
            "LAKE ETL STARTED | staging_records=%s",
            staging_count,
        )

        if staging_count == 0:
            raise ValueError(
                "analytics.stg_processed_transactions is empty."
            )

        # --------------------------------------------------
        # Make sure every staging transaction exists in the
        # operational transactions table.
        # --------------------------------------------------

        unmatched_count = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM analytics.stg_processed_transactions s
                LEFT JOIN transactions t
                    ON t.id::text = s.transaction_id
                WHERE t.id IS NULL
                """
            )
        ).scalar_one()

        if unmatched_count > 0:
            raise ValueError(
                f"Found {unmatched_count} staging transaction(s) "
                "without a matching operational transaction."
            )

        # --------------------------------------------------
        # Read staging records and enrich them.
        #
        # Staging provides the processed lake data.
        # Operational transactions provide the authoritative
        # status and timestamp needed by the fact table.
        # --------------------------------------------------

        staging_transactions = db.execute(
            text(
                """
                SELECT
                    s.transaction_id AS id,
                    s.customer_id,
                    s.amount,
                    s.currency,
                    s.merchant_name,
                    s.merchant_category,
                    s.location,
                    s.device_id,

                    t.status,

                    COALESCE(
                        t.created_at,
                        s.occurred_at
                    ) AS created_at

                FROM analytics.stg_processed_transactions s

                INNER JOIN transactions t
                    ON t.id::text = s.transaction_id

                ORDER BY
                    s.transaction_date,
                    s.transaction_id
                """
            )
        ).mappings().all()

        logger.info(
            "LAKE ETL | enriched_transactions=%s",
            len(staging_transactions),
        )

        # --------------------------------------------------
        # Load dimensions and fact table
        # --------------------------------------------------

        for transaction in staging_transactions:

            load_fact_transaction(
                db,
                transaction,
            )

            records_processed += 1

        # --------------------------------------------------
        # Determine last processed timestamp
        # --------------------------------------------------

        last_processed_timestamp = None

        if staging_transactions:
            last_processed_timestamp = (
                staging_transactions[-1]["created_at"]
            )

        # --------------------------------------------------
        # Update ETL metadata
        # --------------------------------------------------

        db.execute(
            text(
                """
                INSERT INTO analytics.etl_metadata (
                    pipeline_name,
                    last_processed_timestamp,
                    last_run_timestamp,
                    records_processed,
                    pipeline_status,
                    error_message
                )
                VALUES (
                    :pipeline_name,
                    :last_processed_timestamp,
                    :last_run_timestamp,
                    :records_processed,
                    :pipeline_status,
                    NULL
                )
                ON CONFLICT (pipeline_name)
                DO UPDATE SET
                    last_processed_timestamp =
                        EXCLUDED.last_processed_timestamp,
                    last_run_timestamp =
                        EXCLUDED.last_run_timestamp,
                    records_processed =
                        EXCLUDED.records_processed,
                    pipeline_status =
                        EXCLUDED.pipeline_status,
                    error_message = NULL
                """
            ),
            {
                "pipeline_name": pipeline_name,
                "last_processed_timestamp":
                    last_processed_timestamp,
                "last_run_timestamp": started_at,
                "records_processed": records_processed,
                "pipeline_status": "SUCCESS",
            },
        )

        db.commit()

        logger.info(
            "LAKE ETL COMPLETED | records_processed=%s",
            records_processed,
        )

        return {
            "pipeline": pipeline_name,
            "status": "SUCCESS",
            "source": (
                "analytics.stg_processed_transactions"
            ),
            "records_processed": records_processed,
            "last_processed_timestamp": (
                last_processed_timestamp.isoformat()
                if last_processed_timestamp
                else None
            ),
            "completed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

    except Exception as exc:

        db.rollback()

        logger.exception(
            "LAKE ETL FAILED"
        )

        # --------------------------------------------------
        # Record failure in ETL metadata
        # --------------------------------------------------

        db.execute(
            text(
                """
                INSERT INTO analytics.etl_metadata (
                    pipeline_name,
                    last_run_timestamp,
                    records_processed,
                    pipeline_status,
                    error_message
                )
                VALUES (
                    :pipeline_name,
                    :last_run_timestamp,
                    :records_processed,
                    :pipeline_status,
                    :error_message
                )
                ON CONFLICT (pipeline_name)
                DO UPDATE SET
                    last_run_timestamp =
                        EXCLUDED.last_run_timestamp,
                    records_processed =
                        EXCLUDED.records_processed,
                    pipeline_status =
                        EXCLUDED.pipeline_status,
                    error_message =
                        EXCLUDED.error_message
                """
            ),
            {
                "pipeline_name": pipeline_name,
                "last_run_timestamp": started_at,
                "records_processed": records_processed,
                "pipeline_status": "FAILED",
                "error_message": str(exc),
            },
        )

        db.commit()

        raise