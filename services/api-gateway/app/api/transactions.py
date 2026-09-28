from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
)
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
async def get_transactions():

    try:
        return await list_transactions()

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Transaction Service unavailable: {exc}",
        )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
async def get_transaction_by_id(
    transaction_id: UUID,
):

    try:
        return await get_transaction(
            str(transaction_id)
        )

    except Exception as exc:

        if "404" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found.",
            )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Transaction Service unavailable: {exc}",
        )


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction_endpoint(
    transaction_data: TransactionCreate,
):

    try:

        return await create_transaction(
            transaction_data.model_dump(
                mode="json"
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Transaction Service unavailable: {exc}",
        )