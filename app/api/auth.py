from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.database.connection import get_db
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    statement = select(User).where(
        User.email == credentials.email
    )

    user = db.scalar(statement)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    if not verify_password(
        credentials.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role,
        secret_key=settings.jwt_secret_key,
        expires_minutes=settings.access_token_expire_minutes,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
