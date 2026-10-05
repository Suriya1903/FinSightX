from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
)
from app.services.audit_service import publish_audit_event
from app.services.transaction_client import (
    create_transaction,
    get_transaction,
    list_transactions,
)


router = APIRouter(
    prefix="/api/v1/transactions",
    tags=["Transactions"],
)


@router.get(
    "",
    response_model=list[TransactionResponse],
)
async def get_transactions(
    current_user: dict = Depends(get_current_user),
):

    try:

        transactions = await list_transactions()

        publish_audit_event(
            user_id=current_user["user_id"],
            role=current_user["role"],
            action="LIST_TRANSACTIONS",
            resource_type="transaction",
            result="SUCCESS",
        )

        return transactions

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Transaction Service unavailable: {exc}"
            ),
        ) from exc


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
async def get_transaction_by_id(
    transaction_id: UUID,
    current_user: dict = Depends(get_current_user),
):

    try:

        transaction = await get_transaction(
            str(transaction_id)
        )

        publish_audit_event(
            user_id=current_user["user_id"],
            role=current_user["role"],
            action="GET_TRANSACTION",
            resource_type="transaction",
            resource_id=str(transaction_id),
            result="SUCCESS",
        )

        return transaction

    except Exception as exc:

        if "404" in str(exc):

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found.",
            ) from exc

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                f"Transaction Service unavailable: {exc}"
            ),
        ) from exc


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction_endpoint(
    transaction_data: TransactionCreate,
    current_user: dict = Depends(get_current_user),
):

    try:

        transaction = await create_transaction(
            transaction_data.model_dump(
                mode="json"
            )
        )

        publish_audit_event(
            user_id=current_user["user_id"],
            role=current_user["role"],
            action="CREATE_TRANSACTION",
            resource_type="transaction",
            resource_id=str(transaction["id"]),
            result="SUCCESS",
            details={
                "amount": transaction.get("amount"),
                "currency": transaction.get("currency"),
                "merchant_name": transaction.get(
                    "merchant_name"
                ),
                "merchant_category": transaction.get(
                    "merchant_category"
                ),
            },
        )

        return transaction

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                f"Transaction Service unavailable: {exc}"
            ),
        ) from exc