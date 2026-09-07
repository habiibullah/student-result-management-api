from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    account_type = current_user.role

    if current_user.role == "admin":
        if current_user.school_id is None:
            account_type = "platform_admin"
        else:
            account_type = "school_admin"

    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "account_type": account_type,
        "school_id": current_user.school_id,
        "is_active": current_user.is_active,
    }
