"""
FinSightX - Synthetic Fraud Training Dataset Generator

Generates a reproducible historical transaction dataset for supervised
fraud-model training.

Important:
- This dataset is separate from the operational warehouse.
- It is used only for ML training experiments.
- Fraud labels are generated from explicit transaction-risk patterns.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = PROJECT_ROOT / "ml" / "training"
OUTPUT_FILE = OUTPUT_DIR / "fraud_training_dataset.parquet"

RANDOM_SEED = 42
NUMBER_OF_RECORDS = 10000


# -------------------------------------------------------------------
# Generator
# -------------------------------------------------------------------


def generate_dataset(
    number_of_records: int = NUMBER_OF_RECORDS,
    random_seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Generate a synthetic historical fraud dataset."""

    rng = np.random.default_rng(random_seed)

    # ---------------------------------------------------------------
    # Customer IDs
    # ---------------------------------------------------------------

    customer_ids = [
        f"CUST-{index:05d}"
        for index in range(1, 1001)
    ]

    customers = rng.choice(
        customer_ids,
        size=number_of_records,
    )

    # ---------------------------------------------------------------
    # Transaction amounts
    #
    # Log-normal distribution creates realistic skew:
    # most transactions are smaller while a smaller number are large.
    # ---------------------------------------------------------------

    amounts = rng.lognormal(
        mean=np.log(3500),
        sigma=1.0,
        size=number_of_records,
    )

    amounts = np.clip(
        amounts,
        100,
        200000,
    ).round(2)

    # ---------------------------------------------------------------
    # Merchant categories
    # ---------------------------------------------------------------

    merchant_categories_list = [
        "Shopping",
        "E-Commerce",
        "Travel",
        "Food",
        "Entertainment",
        "Healthcare",
        "Utilities",
        "Crypto",
        "Money Transfer",
        "Gambling",
    ]

    # These are the intended relative weights.
    # They do not have to add up to exactly 1.0 because we normalize
    # them below.
    merchant_probabilities = np.array(
        [
            0.18,
            0.18,
            0.08,
            0.10,
            0.08,
            0.07,
            0.08,
            0.07,
            0.09,
            0.05,
        ],
        dtype=float,
    )

    # Normalize probabilities so they always sum exactly to 1.
    merchant_probabilities = (
        merchant_probabilities
        / merchant_probabilities.sum()
    )

    merchant_categories = rng.choice(
        merchant_categories_list,
        size=number_of_records,
        p=merchant_probabilities,
    )

    # ---------------------------------------------------------------
    # Merchant names
    # ---------------------------------------------------------------

    merchant_map = {
        "Shopping": "Retail Store",
        "E-Commerce": "Online Marketplace",
        "Travel": "Travel Platform",
        "Food": "Food Delivery",
        "Entertainment": "Entertainment Platform",
        "Healthcare": "Healthcare Provider",
        "Utilities": "Utility Provider",
        "Crypto": "Crypto Exchange",
        "Money Transfer": "Money Transfer Service",
        "Gambling": "Online Casino",
    }

    merchant_names = np.array(
        [
            merchant_map[category]
            for category in merchant_categories
        ]
    )

    # ---------------------------------------------------------------
    # Transaction timestamps
    # ---------------------------------------------------------------

    start_timestamp = pd.Timestamp(
        "2025-01-01",
        tz="UTC",
    )

    end_timestamp = pd.Timestamp(
        "2026-09-22",
        tz="UTC",
    )

    total_seconds = int(
        (
            end_timestamp
            - start_timestamp
        ).total_seconds()
    )

    random_seconds = rng.integers(
        0,
        total_seconds,
        size=number_of_records,
    )

    transaction_created_at = (
        start_timestamp
        + pd.to_timedelta(
            random_seconds,
            unit="s",
        )
    )

    # ---------------------------------------------------------------
    # Device and location
    # ---------------------------------------------------------------

    device_ids = np.array(
        [
            f"device-{index:04d}"
            for index in rng.integers(
                1,
                3001,
                size=number_of_records,
            )
        ]
    )

    locations = rng.choice(
        [
            "Chennai",
            "Bengaluru",
            "Mumbai",
            "Delhi",
            "Hyderabad",
            "Pune",
            "Kolkata",
        ],
        size=number_of_records,
    )

    # ---------------------------------------------------------------
    # Device/location availability
    # ---------------------------------------------------------------

    missing_device = (
        rng.random(number_of_records) < 0.03
    )

    missing_location = (
        rng.random(number_of_records) < 0.02
    )

    device_ids[missing_device] = ""
    locations[missing_location] = ""

    # ---------------------------------------------------------------
    # Basic transaction attributes
    # ---------------------------------------------------------------

    transaction_status = rng.choice(
        [
            "COMPLETED",
            "PENDING",
            "FAILED",
        ],
        size=number_of_records,
        p=[
            0.82,
            0.13,
            0.05,
        ],
    )

    currency = np.array(
        ["INR"] * number_of_records
    )

    # ---------------------------------------------------------------
    # Time-based features
    # ---------------------------------------------------------------

    transaction_hour = (
        transaction_created_at.hour
    )

    is_weekend = (
        transaction_created_at.dayofweek >= 5
    ).astype(int)

    is_night_transaction = (
        (transaction_hour < 6)
        | (transaction_hour >= 22)
    ).astype(int)

    # ---------------------------------------------------------------
    # Suspicious transaction signals
    # ---------------------------------------------------------------

    high_risk_category = np.isin(
        merchant_categories,
        [
            "Crypto",
            "Money Transfer",
            "Gambling",
        ],
    ).astype(int)

    high_amount = (
        amounts >= 50000
    ).astype(int)

    suspicious_time = (
        is_night_transaction
    )

    missing_device_signal = (
        missing_device.astype(int)
    )

    missing_location_signal = (
        missing_location.astype(int)
    )

    # ---------------------------------------------------------------
    # Customer velocity
    #
    # Simulates the number of recent transactions made by a customer.
    # ---------------------------------------------------------------

    transaction_velocity = rng.poisson(
        lam=2.0,
        size=number_of_records,
    )

    velocity_burst = (
        transaction_velocity >= 5
    ).astype(int)

    # ---------------------------------------------------------------
    # Amount velocity
    # ---------------------------------------------------------------

    recent_transaction_amount = (
        amounts
        * rng.uniform(
            0.5,
            3.0,
            size=number_of_records,
        )
    ).round(2)

    high_velocity_amount = (
        recent_transaction_amount >= 50000
    ).astype(int)

    # ---------------------------------------------------------------
    # Synthetic fraud risk score
    #
    # The scoring logic intentionally resembles the rule-based
    # fraud service already implemented in FinSightX.
    # ---------------------------------------------------------------

    risk_score = (
        high_amount * 60
        + (
            amounts >= 20000
        ).astype(int) * 30
        + high_risk_category * 25
        + missing_device_signal * 15
        + missing_location_signal * 10
        + velocity_burst * 30
        + high_velocity_amount * 25
        + suspicious_time * 10
    )

    risk_score = np.clip(
        risk_score,
        0,
        100,
    )

    # ---------------------------------------------------------------
    # Add realistic label noise
    #
    # A small amount of noise prevents the ML model from simply
    # memorizing a perfectly deterministic rule.
    # ---------------------------------------------------------------

    noise_mask = (
        rng.random(number_of_records) < 0.02
    )

    risk_score[noise_mask] = np.clip(
        risk_score[noise_mask]
        + rng.integers(
            -25,
            26,
            size=noise_mask.sum(),
        ),
        0,
        100,
    )

    # ---------------------------------------------------------------
    # Fraud label
    #
    # HIGH-risk transactions become positive examples.
    # ---------------------------------------------------------------

    fraud_label = (
        risk_score >= 60
    ).astype(int)

    # ---------------------------------------------------------------
    # Risk category
    # ---------------------------------------------------------------

    risk_level = np.select(
        [
            risk_score >= 60,
            risk_score >= 30,
        ],
        [
            "HIGH",
            "MEDIUM",
        ],
        default="LOW",
    )

    # ---------------------------------------------------------------
    # Feature engineering columns
    # ---------------------------------------------------------------

    amount_band_code = pd.cut(
        amounts,
        bins=[
            -float("inf"),
            1000,
            10000,
            50000,
            float("inf"),
        ],
        labels=[
            0,
            1,
            2,
            3,
        ],
    ).astype(int)

    has_device = (
        device_ids != ""
    ).astype(int)

    has_location = (
        locations != ""
    ).astype(int)

    is_pending = (
        transaction_status == "PENDING"
    ).astype(int)

    customer_is_active = np.ones(
        number_of_records,
        dtype=int,
    )

    is_inr = np.ones(
        number_of_records,
        dtype=int,
    )

    # ---------------------------------------------------------------
    # Build DataFrame
    # ---------------------------------------------------------------

    dataframe = pd.DataFrame(
        {
            "transaction_id": [
                f"TRAIN-{index:08d}"
                for index in range(
                    1,
                    number_of_records + 1,
                )
            ],
            "customer_id": customers,
            "amount": amounts,
            "amount_band_code": amount_band_code,
            "is_high_risk_merchant_category": high_risk_category,
            "has_device": has_device,
            "has_location": has_location,
            "customer_is_active": customer_is_active,
            "is_inr": is_inr,
            "is_pending": is_pending,
            "transaction_hour": transaction_hour,
            "transaction_day_of_week": (
                transaction_created_at.dayofweek
            ),
            "is_weekend": is_weekend,
            "is_night_transaction": (
                is_night_transaction
            ),
            "transaction_velocity": (
                transaction_velocity
            ),
            "recent_transaction_amount": (
                recent_transaction_amount
            ),
            "high_velocity_amount": (
                high_velocity_amount
            ),
            "risk_score_rule_based": risk_score,
            "fraud_label": fraud_label,
            "risk_level": risk_level,
            "merchant_name": merchant_names,
            "merchant_category": merchant_categories,
            "device_id": device_ids,
            "location_name": locations,
            "currency": currency,
            "transaction_status": transaction_status,
            "transaction_created_at": (
                transaction_created_at
            ),
        }
    )

    return dataframe


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("FinSightX Synthetic Fraud Training Dataset Generator")
    print("=" * 70)

    print()
    print(f"Random seed : {RANDOM_SEED}")
    print(f"Records     : {NUMBER_OF_RECORDS}")
    print(f"Output      : {OUTPUT_FILE}")
    print()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = generate_dataset()

    dataframe.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print("Dataset generated successfully.")
    print()

    print("Dataset shape:")
    print(f"Rows    : {len(dataframe)}")
    print(f"Columns : {len(dataframe.columns)}")

    print()
    print("Fraud label distribution:")

    print(
        dataframe["fraud_label"]
        .value_counts()
        .sort_index()
        .rename(
            index={
                0: "LEGITIMATE",
                1: "FRAUD",
            }
        )
    )

    print()
    print("Risk level distribution:")

    print(
        dataframe["risk_level"]
        .value_counts()
    )

    print()
    print("Amount statistics:")

    print(
        dataframe["amount"].describe()
    )

    print()
    print("Fraud rate:")

    print(
        f"{dataframe['fraud_label'].mean() * 100:.2f}%"
    )

    print()
    print("Sample records:")

    print(
        dataframe[
            [
                "transaction_id",
                "amount",
                "merchant_category",
                "transaction_hour",
                "transaction_velocity",
                "risk_score_rule_based",
                "risk_level",
                "fraud_label",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print()
    print("Saved to:")

    print(OUTPUT_FILE)

    print()
    print("=" * 70)
    print("Training dataset generation completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()