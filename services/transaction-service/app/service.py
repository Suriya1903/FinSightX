from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.events import publish_transaction_created
from app.models import Transaction
from app.schemas import TransactionCreate


def create_transaction(
    db: Session,
    transaction_data: TransactionCreate,
) -> Transaction:

    transaction = Transaction(
        customer_id=transaction_data.customer_id,
        amount=transaction_data.amount,
        currency=transaction_data.currency.upper(),
        merchant_name=transaction_data.merchant_name,
        merchant_category=(
            transaction_data.merchant_category
        ),
        location=transaction_data.location,
        device_id=transaction_data.device_id,
        status="PENDING",
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    publish_transaction_created(
        transaction
    )

    return transaction


def get_transaction(
    db: Session,
    transaction_id: UUID,
):
    return db.scalar(
        select(Transaction).where(
            Transaction.id == transaction_id
        )
    )


def list_transactions(
    db: Session,
):
    return db.scalars(
        select(Transaction).order_by(
            Transaction.created_at.desc()
        )
    ).all()