import json
import os

import psycopg
from psycopg.rows import dict_row


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://finsightx:change_me@postgres:5432/finsightx",
)


def get_connection():
    """
    Create a PostgreSQL connection for fraud assessment persistence.
    """

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
    )


def ensure_ml_columns() -> None:
    """
    Add ML assessment columns to the existing fraud_assessments
    table if they do not already exist.

    This is intentionally idempotent.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                ALTER TABLE fraud_assessments
                ADD COLUMN IF NOT EXISTS
                    ml_prediction VARCHAR(32)
                """
            )

            cursor.execute(
                """
                ALTER TABLE fraud_assessments
                ADD COLUMN IF NOT EXISTS
                    ml_probability DOUBLE PRECISION
                """
            )

            cursor.execute(
                """
                ALTER TABLE fraud_assessments
                ADD COLUMN IF NOT EXISTS
                    ml_risk_level VARCHAR(32)
                """
            )

            cursor.execute(
                """
                ALTER TABLE fraud_assessments
                ADD COLUMN IF NOT EXISTS
                    ml_model_version VARCHAR(64)
                """
            )

        connection.commit()


def save_fraud_assessment(
    event: dict,
    risk_level: str,
    risk_score: int,
    reasons: list[str],
    ml_assessment: dict,
) -> None:
    """
    Persist the rule-based and ML fraud assessment.
    """

    transaction = event["transaction"]

    event_id = event["event_id"]
    transaction_id = transaction["id"]
    customer_id = transaction["customer_id"]

    with get_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO fraud_assessments (
                    event_id,
                    transaction_id,
                    customer_id,
                    risk_level,
                    risk_score,
                    reasons,
                    ml_prediction,
                    ml_probability,
                    ml_risk_level,
                    ml_model_version
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT (event_id)
                DO UPDATE SET
                    risk_level =
                        EXCLUDED.risk_level,
                    risk_score =
                        EXCLUDED.risk_score,
                    reasons =
                        EXCLUDED.reasons,
                    ml_prediction =
                        EXCLUDED.ml_prediction,
                    ml_probability =
                        EXCLUDED.ml_probability,
                    ml_risk_level =
                        EXCLUDED.ml_risk_level,
                    ml_model_version =
                        EXCLUDED.ml_model_version,
                    assessed_at =
                        CURRENT_TIMESTAMP
                """,
                (
                    event_id,
                    transaction_id,
                    customer_id,
                    risk_level,
                    risk_score,
                    json.dumps(reasons),
                    ml_assessment[
                        "prediction"
                    ],
                    ml_assessment[
                        "fraud_probability"
                    ],
                    ml_assessment[
                        "risk_level"
                    ],
                    ml_assessment[
                        "model_version"
                    ],
                ),
            )

        connection.commit()