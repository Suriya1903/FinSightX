from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base, engine, get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    AuthenticationError,
    ConflictError,
    authenticate_user,
    get_token_expiry_seconds,
    register_user,
)


security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FinSightX Auth Service",
    description="Authentication and authorization service for FinSightX.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    return {
        "service": "auth-service",
        "status": "healthy",
    }


@app.get("/")
def root() -> dict:
    return {
        "service": "FinSightX Auth Service",
        "status": "running",
        "version": "1.0.0",
    }


@app.post(
    "/api/v1/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:

    try:
        user = register_user(
            db=db,
            username=request.username,
            email=str(request.email),
            password=request.password,
        )

        return UserResponse.model_validate(user)

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@app.post(
    "/api/v1/auth/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:

    try:
        user, access_token = authenticate_user(
            db=db,
            username=request.username,
            password=request.password,
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=get_token_expiry_seconds(),
            user=UserResponse.model_validate(user),
        )

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        ) from exc


@app.get(
    "/api/v1/auth/me",
    response_model=UserResponse,
)
def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UserResponse:

    try:
        payload = decode_access_token(
            credentials.credentials
        )

        user_id = payload.get("sub")

        if not user_id:
            raise ValueError(
                "Token subject is missing."
            )

        user = db.execute(
            select(User).where(
                User.id == UUID(user_id)
            )
        ).scalar_one_or_none()

        if user is None:
            raise ValueError(
                "User not found."
            )

        if not user.is_active:
            raise ValueError(
                "User account is inactive."
            )

        return UserResponse.model_validate(user)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        ) from exc
