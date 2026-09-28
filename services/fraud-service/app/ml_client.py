from __future__ import annotations

import logging
import os
from typing import Any

import httpx


logger = logging.getLogger("finsightx-fraud-ml")


ML_SERVICE_URL = os.getenv(
    "ML_SERVICE_URL",
    "http://ml-service:8008",
)

ML_PREDICT_TIMEOUT_SECONDS = float(
    os.getenv(
        "ML_PREDICT_TIMEOUT_SECONDS",
        "10",
    )
)


def predict_fraud(
    *,
    amount: float,
    merchant_category: str | None,
    currency: str | None,
    transaction_status: str | None,
    location: str | None,
    device_id: str | None,
    customer_status: str | None,
    transaction_velocity: int,
    recent_transaction_amount: float,
    transaction_hour: int,
    transaction_day_of_week: int,
    is_weekend: int,
) -> dict[str, Any]:
    """
    Call the FinSightX ML Service using the exact feature schema
    expected by the trained Random Forest model.
    """

    amount_band_code = _amount_band_code(amount)

    merchant_category_normalized = (
        (merchant_category or "").strip()
    )

    high_risk_categories = {
        "gambling",
        "crypto",
        "money transfer",
        "gambling/casino",
    }

    is_high_risk_merchant_category = int(
        merchant_category_normalized.lower()
        in high_risk_categories
    )

    has_device = int(
        bool((device_id or "").strip())
    )

    has_location = int(
        bool((location or "").strip())
    )

    customer_is_active = int(
        (customer_status or "").strip().upper()
        == "ACTIVE"
    )

    is_inr = int(
        (currency or "").strip().upper()
        == "INR"
    )

    is_pending = int(
        (transaction_status or "").strip().upper()
        == "PENDING"
    )

    is_night_transaction = int(
        transaction_hour < 6
        or transaction_hour >= 22
    )

    payload = {
        "amount": float(amount),
        "amount_band_code": amount_band_code,
        "is_high_risk_merchant_category":
            is_high_risk_merchant_category,
        "has_device": has_device,
        "has_location": has_location,
        "customer_is_active": customer_is_active,
        "is_inr": is_inr,
        "is_pending": is_pending,
        "transaction_hour": transaction_hour,
        "transaction_day_of_week":
            transaction_day_of_week,
        "is_weekend": is_weekend,
        "is_night_transaction":
            is_night_transaction,
        "transaction_velocity":
            int(transaction_velocity),
        "recent_transaction_amount":
            float(recent_transaction_amount),
        "high_velocity_amount":
            float(recent_transaction_amount),
        "merchant_category":
            merchant_category_normalized or "Unknown",
        "currency":
            (currency or "").strip().upper() or "UNKNOWN",
        "transaction_status":
            (transaction_status or "").strip().upper()
            or "UNKNOWN",
    }

    logger.info(
        "Calling ML service | url=%s | amount=%s | "
        "velocity_count=%s | velocity_amount=%s",
        ML_SERVICE_URL,
        amount,
        transaction_velocity,
        recent_transaction_amount,
    )

    response = httpx.post(
        f"{ML_SERVICE_URL}/api/v1/predict",
        json=payload,
        timeout=ML_PREDICT_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    result = response.json()

    logger.info(
        "ML prediction received | prediction=%s | "
        "probability=%s | risk=%s",
        result.get("prediction"),
        result.get("fraud_probability"),
        result.get("risk_level"),
    )

    return result


def _amount_band_code(amount: float) -> int:
    """
    Match the exact amount-band mapping used during feature
    engineering and model training.

    < 1000       -> 0
    1000-9999    -> 1
    10000-49999  -> 2
    >= 50000     -> 3
    """

    if amount < 1000:
        return 0

    if amount < 10000:
        return 1

    if amount < 50000:
        return 2

    return 3


def calculate_time_features(
    occurred_at: str | None,
) -> tuple[int, int, int]:
    """
    Return:
        transaction_hour,
        transaction_day_of_week,
        is_weekend

    The feature-engineering pipeline uses Monday=0 through Sunday=6.
    """

    from datetime import datetime, timezone

    if not occurred_at:
        current = datetime.now(timezone.utc)
    else:
        normalized = occurred_at.replace(
            "Z",
            "+00:00",
        )

        current = datetime.fromisoformat(
            normalized
        )

        if current.tzinfo is None:
            current = current.replace(
                tzinfo=timezone.utc
            )

    transaction_hour = current.hour
    transaction_day_of_week = current.weekday()
    is_weekend = int(
        transaction_day_of_week >= 5
    )

    return (
        transaction_hour,
        transaction_day_of_week,
        is_weekend,
    )