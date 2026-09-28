"""
FinSightX - Fraud Detection Feature Engineering

Reads transaction data from the PostgreSQL analytics warehouse,
creates ML-ready fraud detection features, and writes the resulting
feature dataset to a local Parquet file.

This stage intentionally does NOT train a model.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

FEATURE_OUTPUT_DIR = PROJECT_ROOT / "ml" / "features"
FEATURE_OUTPUT_FILE = FEATURE_OUTPUT_DIR / "fraud_features.parquet"


# -------------------------------------------------------------------
# Database configuration
# -------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://finsightx:change_me@localhost:5434/finsightx",
)


# -------------------------------------------------------------------
# SQL query
# -------------------------------------------------------------------

FEATURE_QUERY = text(
    """
    SELECT
        f.transaction_id,
        f.customer_key,
        f.merchant_key,
        f.device_key,
        f.location_key,
        f.date_key,

        f.amount,
        f.currency,
        f.transaction_status,
        f.risk_level,
        f.risk_score,
        f.transaction_created_at,

        c.customer_id,
        c.country AS customer_country,
        c.status AS customer_status,

        m.merchant_name,
        m.merchant_category,

        d.device_id,

        l.location_name,

        dd.full_date,
        dd.day_number,
        dd.month_number,
        dd.quarter_number,
        dd.year_number,
        dd.day_of_week_number,
        dd.is_weekend

    FROM analytics.fact_transactions f

    INNER JOIN analytics.dim_customer c
        ON f.customer_key = c.customer_key

    INNER JOIN analytics.dim_merchant m
        ON f.merchant_key = m.merchant_key

    LEFT JOIN analytics.dim_device d
        ON f.device_key = d.device_key

    LEFT JOIN analytics.dim_location l
        ON f.location_key = l.location_key

    INNER JOIN analytics.dim_date dd
        ON f.date_key = dd.date_key

    ORDER BY f.transaction_created_at
    """
)


# -------------------------------------------------------------------
# Feature engineering
# -------------------------------------------------------------------


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create ML features from warehouse transaction data."""

    if df.empty:
        raise ValueError("No transaction records were returned from the warehouse.")

    result = df.copy()

    # ---------------------------------------------------------------
    # Basic numeric features
    # ---------------------------------------------------------------

    result["amount"] = pd.to_numeric(
        result["amount"],
        errors="coerce",
    ).fillna(0.0)

    result["risk_score"] = pd.to_numeric(
        result["risk_score"],
        errors="coerce",
    )

    # ---------------------------------------------------------------
    # Amount-based features
    # ---------------------------------------------------------------

    result["amount_log"] = (result["amount"] + 1).apply(
        lambda value: __import__("math").log(value)
    )

    result["amount_band_code"] = pd.cut(
        result["amount"],
        bins=[-float("inf"), 1000, 10000, 50000, float("inf")],
        labels=[0, 1, 2, 3],
    ).astype(int)

    # ---------------------------------------------------------------
    # Time-based features
    # ---------------------------------------------------------------

    result["transaction_created_at"] = pd.to_datetime(
        result["transaction_created_at"],
        utc=True,
        errors="coerce",
    )

    result["transaction_hour"] = (
        result["transaction_created_at"].dt.hour
    )

    result["transaction_day_of_week"] = (
        result["transaction_created_at"].dt.dayofweek
    )

    result["is_weekend"] = result["is_weekend"].astype(int)

    result["is_night_transaction"] = (
        (result["transaction_hour"] < 6)
        | (result["transaction_hour"] >= 22)
    ).astype(int)

    # ---------------------------------------------------------------
    # Merchant features
    # ---------------------------------------------------------------

    high_risk_categories = {
        "Gambling",
        "Crypto",
        "Money Transfer",
        "Gambling/Casino",
    }

    result["is_high_risk_merchant_category"] = (
        result["merchant_category"]
        .fillna("")
        .astype(str)
        .str.strip()
        .isin(high_risk_categories)
        .astype(int)
    )

    # ---------------------------------------------------------------
    # Device / location availability features
    # ---------------------------------------------------------------

    result["has_device"] = (
        result["device_id"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        .astype(int)
    )

    result["has_location"] = (
        result["location_name"]
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
        .astype(int)
    )

    # ---------------------------------------------------------------
    # Customer features
    # ---------------------------------------------------------------

    result["customer_is_active"] = (
        result["customer_status"]
        .fillna("")
        .astype(str)
        .str.upper()
        .eq("ACTIVE")
        .astype(int)
    )

    # ---------------------------------------------------------------
    # Currency feature
    # ---------------------------------------------------------------

    result["is_inr"] = (
        result["currency"]
        .fillna("")
        .astype(str)
        .str.upper()
        .eq("INR")
        .astype(int)
    )

    # ---------------------------------------------------------------
    # Transaction status features
    # ---------------------------------------------------------------

    result["is_pending"] = (
        result["transaction_status"]
        .fillna("")
        .astype(str)
        .str.upper()
        .eq("PENDING")
        .astype(int)
    )

    # ---------------------------------------------------------------
    # ML target
    #
    # 1 = confirmed HIGH risk
    # 0 = confirmed LOW/MEDIUM risk
    # NaN = not assessed yet
    #
    # We do NOT treat NOT_ASSESSED as legitimate negative labels.
    # ---------------------------------------------------------------

    result["fraud_label"] = result["risk_level"].map(
        {
            "HIGH": 1,
            "MEDIUM": 0,
            "LOW": 0,
        }
    )

    # ---------------------------------------------------------------
    # Select final ML features
    # ---------------------------------------------------------------

    feature_columns = [
        "transaction_id",
        "customer_id",
        "amount",
        "amount_log",
        "amount_band_code",
        "is_high_risk_merchant_category",
        "has_device",
        "has_location",
        "customer_is_active",
        "is_inr",
        "is_pending",
        "transaction_hour",
        "transaction_day_of_week",
        "is_weekend",
        "is_night_transaction",
        "fraud_label",
        "risk_level",
        "risk_score",
        "merchant_name",
        "merchant_category",
        "location_name",
        "device_id",
        "transaction_created_at",
    ]

    return result[feature_columns]


# -------------------------------------------------------------------
# Main pipeline
# -------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("FinSightX Fraud Feature Engineering")
    print("=" * 70)

    print(f"Database: {DATABASE_URL}")
    print(f"Output:   {FEATURE_OUTPUT_FILE}")
    print()

    FEATURE_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

    print("Reading transactions from analytics warehouse...")

    with engine.connect() as connection:
        df = pd.read_sql(
            FEATURE_QUERY,
            connection,
        )

    print(f"Warehouse records loaded: {len(df)}")

    features = create_features(df)

    print()
    print("Feature engineering completed.")
    print(f"Feature records: {len(features)}")
    print(f"Feature columns: {len(features.columns)}")

    confirmed_labels = features["fraud_label"].notna().sum()
    unassessed_records = features["fraud_label"].isna().sum()

    print()
    print("Label summary:")
    print(f"Confirmed labelled records : {confirmed_labels}")
    print(f"Unassessed records        : {unassessed_records}")

    if confirmed_labels > 0:
        print()
        print("Confirmed label distribution:")
        print(
            features.loc[
                features["fraud_label"].notna(),
                "fraud_label",
            ].value_counts(dropna=False)
        )

    features.to_parquet(
        FEATURE_OUTPUT_FILE,
        index=False,
    )

    print()
    print("Feature dataset written successfully.")
    print(FEATURE_OUTPUT_FILE)

    print()
    print("Sample feature records:")
    print(
        features[
            [
                "transaction_id",
                "amount",
                "amount_band_code",
                "is_high_risk_merchant_category",
                "has_device",
                "has_location",
                "transaction_hour",
                "is_weekend",
                "fraud_label",
            ]
        ].head(10).to_string(index=False)
    )

    print()
    print("=" * 70)
    print("Feature engineering pipeline completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()