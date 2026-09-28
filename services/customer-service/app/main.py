from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CustomerCreate, CustomerResponse
from app.service import (
    create_customer,
    get_customer,
    list_customers,
)


app = FastAPI(
    title="FinSightX Customer Service",
    description="Customer management microservice for FinSightX.",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {
        "service": "customer-service",
        "status": "healthy",
    }


@app.get("/api/v1/customers")
async def get_customers(
    db: Session = Depends(get_db),
) -> list[CustomerResponse]:

    customers = list_customers(db)

    return customers


@app.get(
    "/api/v1/customers/{customer_id}",
)
async def get_customer_by_id(
    customer_id: UUID,
    db: Session = Depends(get_db),
) -> CustomerResponse:

    customer = get_customer(
        db=db,
        customer_id=customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    return customer


@app.post(
    "/api/v1/customers",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_endpoint(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
) -> CustomerResponse:

    try:
        customer = create_customer(
            db=db,
            customer_data=customer_data,
        )

        return customer

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@app.get("/")
async def root():
    return {
        "service": "FinSightX Customer Service",
        "status": "running",
        "version": "1.0.0",
    }