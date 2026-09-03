from fastapi import APIRouter, Depends

from app.core.dependencies import (
    require_admin,
    require_teacher,
    require_student,
)
from app.models import User


router = APIRouter(
    prefix="/api",
    tags=["Authorization"],
)


@router.get("/admin/test")
def admin_test(
    current_user: User = Depends(require_admin),
):
    return {
        "message": "Admin access granted",
        "user_id": current_user.id,
        "role": current_user.role,
    }


@router.get("/teachers/test")
def teacher_test(
    current_user: User = Depends(require_teacher),
):
    return {
        "message": "Teacher access granted",
        "user_id": current_user.id,
        "role": current_user.role,
    }


@router.get("/students/test")
def student_test(
    current_user: User = Depends(require_student),
):
    return {
        "message": "Student access granted",
        "user_id": current_user.id,
        "role": current_user.role,
    }
