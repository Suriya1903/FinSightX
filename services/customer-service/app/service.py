from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer
from app.schemas import CustomerCreate


def create_customer(
    db: Session,
    customer_data: CustomerCreate,
) -> Customer:

    existing_customer = db.scalar(
        select(Customer).where(
            Customer.email == customer_data.email
        )
    )

    if existing_customer:
        raise ValueError(
            "A customer with this email already exists."
        )

    customer = Customer(
        full_name=customer_data.full_name,
        email=str(customer_data.email),
        phone=customer_data.phone,
        country=customer_data.country,
        status="ACTIVE",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customer(
    db: Session,
    customer_id,
):
    return db.scalar(
        select(Customer).where(
            Customer.id == customer_id
        )
    )


def list_customers(
    db: Session,
):
    return db.scalars(
        select(Customer).order_by(
            Customer.created_at.desc()
        )
    ).all()