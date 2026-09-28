from typing import Literal

from pydantic import BaseModel, Field


class FraudPredictionRequest(BaseModel):
    """
    Input schema matching the exact 18 features used by the
    trained FinSightX Random Forest pipeline.
    """

    amount: float = Field(..., ge=0)

    amount_band_code: int = Field(
        ...,
        ge=0,
        le=3,
    )

    is_high_risk_merchant_category: int = Field(
        ...,
        ge=0,
        le=1,
    )

    has_device: int = Field(
        ...,
        ge=0,
        le=1,
    )

    has_location: int = Field(
        ...,
        ge=0,
        le=1,
    )

    customer_is_active: int = Field(
        ...,
        ge=0,
        le=1,
    )

    is_inr: int = Field(
        ...,
        ge=0,
        le=1,
    )

    is_pending: int = Field(
        ...,
        ge=0,
        le=1,
    )

    transaction_hour: int = Field(
        ...,
        ge=0,
        le=23,
    )

    transaction_day_of_week: int = Field(
        ...,
        ge=0,
        le=6,
    )

    is_weekend: int = Field(
        ...,
        ge=0,
        le=1,
    )

    is_night_transaction: int = Field(
        ...,
        ge=0,
        le=1,
    )

    transaction_velocity: int = Field(
        ...,
        ge=0,
    )

    recent_transaction_amount: float = Field(
        ...,
        ge=0,
    )

    high_velocity_amount: float = Field(
        ...,
        ge=0,
    )

    merchant_category: str = Field(
        ...,
        min_length=1,
    )

    currency: str = Field(
        ...,
        min_length=1,
    )

    transaction_status: str = Field(
        ...,
        min_length=1,
    )


class FraudPredictionResponse(BaseModel):
    model_name: str
    model_version: str
    prediction: Literal["LEGITIMATE", "FRAUD"]
    fraud_probability: float
    legitimate_probability: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    model_threshold: float


class ModelInfoResponse(BaseModel):
    service: str
    model_name: str
    model_version: str
    model_type: str
    feature_count: int
    status: str