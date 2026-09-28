from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
)

from app.services.customer_service import (
    create_customer,
    get_customer,
    list_customers,
)


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Customers"],
)


@router.get(
    "",
    response_model=list[CustomerResponse],
)
async def get_customers():

    try:
        return await list_customers()

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Customer Service unavailable: {exc}",
        )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
async def get_customer_by_id(
    customer_id: UUID,
):

    try:
        return await get_customer(
            str(customer_id)
        )

    except Exception as exc:

        if "404" in str(exc):

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found.",
            )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Customer Service unavailable: {exc}",
        )


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_endpoint(
    customer_data: CustomerCreate,
):

    try:

        return await create_customer(
            customer_data.model_dump(
                mode="json"
            )
        )

    except Exception as exc:

        if "409" in str(exc):

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A customer with this email already exists.",
            )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Customer Service unavailable: {exc}",
        )