from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin, require_teacher
from app.database.connection import get_db
from app.models import (
    AcademicSession,
    Class,
    ClassTeacherAssignment,
    Teacher,
    User,
)
from app.schemas.class_teacher_assignment import (
    ClassTeacherAssignmentCreate,
    ClassTeacherAssignmentResponse,
)


router = APIRouter(
    prefix="/api/class-teacher-assignments",
    tags=["Class Teacher Assignments"],
)


@router.post(
    "",
    response_model=ClassTeacherAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class_teacher_assignment(
    assignment_data: ClassTeacherAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    teacher = db.scalar(
        select(Teacher).where(
            Teacher.id == assignment_data.teacher_id,
            Teacher.school_id == current_user.school_id,
        )
    )

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    class_ = db.scalar(
        select(Class).where(
            Class.id == assignment_data.class_id,
            Class.school_id == current_user.school_id,
        )
    )

    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id
            == assignment_data.academic_session_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    existing_assignment = db.scalar(
        select(ClassTeacherAssignment).where(
            ClassTeacherAssignment.class_id
            == assignment_data.class_id,
            ClassTeacherAssignment.academic_session_id
            == assignment_data.academic_session_id,
        )
    )

    if existing_assignment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This class already has a class teacher "
                "for the selected academic session"
            ),
        )

    assignment = ClassTeacherAssignment(
        teacher_id=assignment_data.teacher_id,
        class_id=assignment_data.class_id,
        academic_session_id=assignment_data.academic_session_id,
    )

    db.add(assignment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This class already has a class teacher "
                "for the selected academic session"
            ),
        )

    db.refresh(assignment)

    return assignment


@router.get(
    "",
    response_model=list[ClassTeacherAssignmentResponse],
)
def get_class_teacher_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    assignments = db.scalars(
        select(ClassTeacherAssignment)
        .join(
            Teacher,
            ClassTeacherAssignment.teacher_id == Teacher.id,
        )
        .join(
            Class,
            ClassTeacherAssignment.class_id == Class.id,
        )
        .join(
            AcademicSession,
            ClassTeacherAssignment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Teacher.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
        .order_by(ClassTeacherAssignment.id)
    ).all()

    return assignments


@router.get(
    "/me",
    response_model=list[ClassTeacherAssignmentResponse],
)
def get_my_class_teacher_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    assignments = db.scalars(
        select(ClassTeacherAssignment)
        .join(
            Teacher,
            ClassTeacherAssignment.teacher_id == Teacher.id,
        )
        .join(
            Class,
            ClassTeacherAssignment.class_id == Class.id,
        )
        .join(
            AcademicSession,
            ClassTeacherAssignment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Teacher.user_id == current_user.id,
            Teacher.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
        .order_by(ClassTeacherAssignment.id)
    ).all()

    return assignments


@router.get(
    "/{assignment_id}",
    response_model=ClassTeacherAssignmentResponse,
)
def get_class_teacher_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    assignment = db.scalar(
        select(ClassTeacherAssignment)
        .join(
            Teacher,
            ClassTeacherAssignment.teacher_id == Teacher.id,
        )
        .join(
            Class,
            ClassTeacherAssignment.class_id == Class.id,
        )
        .join(
            AcademicSession,
            ClassTeacherAssignment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            ClassTeacherAssignment.id == assignment_id,
            Teacher.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class teacher assignment not found",
        )

    return assignment


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_class_teacher_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    assignment = db.scalar(
        select(ClassTeacherAssignment)
        .join(
            Teacher,
            ClassTeacherAssignment.teacher_id == Teacher.id,
        )
        .join(
            Class,
            ClassTeacherAssignment.class_id == Class.id,
        )
        .join(
            AcademicSession,
            ClassTeacherAssignment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            ClassTeacherAssignment.id == assignment_id,
            Teacher.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class teacher assignment not found",
        )

    db.delete(assignment)
    db.commit()

    return None