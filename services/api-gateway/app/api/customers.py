from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
)
from app.services.audit_service import publish_audit_event
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
async def get_customers(
    current_user: dict = Depends(get_current_user),
):

    try:

        customers = await list_customers()

        publish_audit_event(
            user_id=current_user["user_id"],
            role=current_user["role"],
            action="LIST_CUSTOMERS",
            resource_type="customer",
            result="SUCCESS",
        )

        return customers

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                f"Customer Service unavailable: {exc}"
            ),
        ) from exc


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
async def get_customer_by_id(
    customer_id: UUID,
    current_user: dict = Depends(get_current_user),
):

    try:

        customer = await get_customer(
            str(customer_id)
        )

        publish_audit_event(
            user_id=current_user["user_id"],
            role=current_user["role"],
            action="GET_CUSTOMER",
            resource_type="customer",
            resource_id=str(customer_id),
            result="SUCCESS",
        )

        return customer

    except Exception as exc:

        if "404" in str(exc):

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found.",
            ) from exc

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                f"Customer Service unavailable: {exc}"
            ),
        ) from exc


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer_endpoint(
    customer_data: CustomerCreate,
    current_user: dict = Depends(get_current_user),
):

    try:

        customer = await create_customer(
            customer_data.model_dump(
                mode="json"
            )
        )

        publish_audit_event(
            user_id=current_user["user_id"],
            role=current_user["role"],
            action="CREATE_CUSTOMER",
            resource_type="customer",
            resource_id=str(customer["id"]),
            result="SUCCESS",
            details={
                "email": customer.get("email"),
                "country": customer.get("country"),
            },
        )

        return customer

    except Exception as exc:

        if "409" in str(exc):

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A customer with this email "
                    "already exists."
                ),
            ) from exc

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                f"Customer Service unavailable: {exc}"
            ),
        ) from exc