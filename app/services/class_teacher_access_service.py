from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.class_teacher_assignment import ClassTeacherAssignment
from app.models.enrollment import Enrollment
from app.models.teacher import Teacher
from app.models.user import User


def require_class_teacher_student_access(
    *,
    db: Session,
    current_user: User,
    student_id: int,
    academic_session_id: int,
) -> None:
    """
    Allow a school administrator, or verify that a teacher is the
    assigned class teacher for the student's enrolled class in the
    selected academic session.
    """

    if current_user.role == "admin":
        return

    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="School admin or class teacher access required",
        )

    teacher = db.scalar(
        select(Teacher).where(
            Teacher.user_id == current_user.id,
            Teacher.school_id == current_user.school_id,
        )
    )

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Class teacher access required",
        )

    has_access = db.scalar(
        select(ClassTeacherAssignment.id)
        .join(
            Enrollment,
            Enrollment.class_id == ClassTeacherAssignment.class_id,
        )
        .where(
            ClassTeacherAssignment.teacher_id == teacher.id,
            ClassTeacherAssignment.academic_session_id
            == academic_session_id,
            Enrollment.student_id == student_id,
            Enrollment.academic_session_id == academic_session_id,
        )
        .limit(1)
    )

    if has_access is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Class teacher access required",
        )