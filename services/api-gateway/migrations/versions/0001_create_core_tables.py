"""create core customer and transaction tables

Revision ID: 0001
Revises:
Create Date: 2026-09-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "full_name",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "phone",
            sa.String(length=30),
            nullable=True,
        ),
        sa.Column(
            "country",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_index(
        "ix_customers_email",
        "customers",
        ["email"],
        unique=False,
    )

    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(18, 2),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
        ),
        sa.Column(
            "merchant_name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "merchant_category",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "location",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "device_id",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_transactions_customer_id",
        "transactions",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_created_at",
        "transactions",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_customer_created_at",
        "transactions",
        ["customer_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transactions_customer_created_at",
        table_name="transactions",
    )

    op.drop_index(
        "ix_transactions_created_at",
        table_name="transactions",
    )

    op.drop_index(
        "ix_transactions_customer_id",
        table_name="transactions",
    )

    op.drop_table("transactions")

    op.drop_index(
        "ix_customers_email",
        table_name="customers",
    )

    op.drop_table("customers")