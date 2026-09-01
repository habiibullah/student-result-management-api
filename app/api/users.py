from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models import User


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }
