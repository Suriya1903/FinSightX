from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    TransactionCreate,
    TransactionResponse,
)
from app.service import (
    create_transaction,
    get_transaction,
    list_transactions,
)


app = FastAPI(
    title="FinSightX Transaction Service",
    description="Transaction management microservice for FinSightX.",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {
        "service": "transaction-service",
        "status": "healthy",
    }


@app.get("/")
async def root():
    return {
        "service": "FinSightX Transaction Service",
        "status": "running",
        "version": "1.0.0",
    }


@app.get(
    "/api/v1/transactions",
    response_model=list[TransactionResponse],
)
async def get_transactions(
    db: Session = Depends(get_db),
):
    return list_transactions(db)


@app.get(
    "/api/v1/transactions/{transaction_id}",
    response_model=TransactionResponse,
)
async def get_transaction_by_id(
    transaction_id: UUID,
    db: Session = Depends(get_db),
):
    transaction = get_transaction(
        db=db,
        transaction_id=transaction_id,
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )

    return transaction


@app.post(
    "/api/v1/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction_endpoint(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_transaction(
            db=db,
            transaction_data=transaction_data,
        )

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create transaction: {exc}",
        )