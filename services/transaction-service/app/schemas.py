from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    customer_id: UUID

    amount: Decimal = Field(
        ...,
        gt=0,
        max_digits=18,
        decimal_places=2,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    merchant_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    merchant_category: str | None = Field(
        default=None,
        max_length=100,
    )

    location: str | None = Field(
        default=None,
        max_length=200,
    )

    device_id: str | None = Field(
        default=None,
        max_length=150,
    )


class TransactionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    customer_id: UUID
    amount: Decimal
    currency: str
    merchant_name: str
    merchant_category: str | None
    location: str | None
    device_id: str | None
    status: str
    created_at: datetime