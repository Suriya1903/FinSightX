from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from app.core.security import get_current_user
from app.services.auth_service import (
    get_authenticated_user,
    login_user,
    register_user,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


bearer_scheme = HTTPBearer(
    auto_error=False
)


class UserRegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: UserRegisterRequest,
):

    response = await register_user(
        request.model_dump(
            mode="json"
        )
    )

    return_response_status = response.status_code

    if return_response_status >= 400:
        raise HTTPException(
            status_code=return_response_status,
            detail=response.text,
        )

    return response.json()


@router.post(
    "/login",
)
async def login(
    request: LoginRequest,
):

    response = await login_user(
        request.model_dump()
    )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    return response.json()


@router.get(
    "/me",
)
async def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    current_user: dict = Depends(
        get_current_user
    ),
):

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    response = await get_authenticated_user(
        credentials.credentials
    )

    if response.status_code >= 400:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    return response.json()