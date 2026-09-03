from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.connection import get_db
from app.models import (
    AcademicSession,
    Class,
    Subject,
    Teacher,
    TeachingAssignment,
    User,
)
from app.schemas.teaching_assignment import (
    TeachingAssignmentCreate,
    TeachingAssignmentResponse,
)

router = APIRouter(
    prefix="/api/teaching-assignments",
    tags=["Teaching Assignments"],
)


@router.post(
    "",
    response_model=TeachingAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_teaching_assignment(
    assignment_data: TeachingAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    teacher = db.scalar(
        select(Teacher).where(
            Teacher.id == assignment_data.teacher_id
        )
    )

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    subject = db.scalar(
        select(Subject).where(
            Subject.id == assignment_data.subject_id
        )
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    class_ = db.scalar(
        select(Class).where(
            Class.id == assignment_data.class_id
        )
    )

    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == assignment_data.academic_session_id
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    existing_assignment = db.scalar(
        select(TeachingAssignment).where(
            (TeachingAssignment.teacher_id == assignment_data.teacher_id)
            & (TeachingAssignment.subject_id == assignment_data.subject_id)
            & (TeachingAssignment.class_id == assignment_data.class_id)
            & (
                TeachingAssignment.academic_session_id
                == assignment_data.academic_session_id
            )
        )
    )

    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This teaching assignment already exists",
        )

    assignment = TeachingAssignment(
        teacher_id=assignment_data.teacher_id,
        subject_id=assignment_data.subject_id,
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
            detail="This teaching assignment already exists",
        )

    db.refresh(assignment)

    return assignment


@router.get(
    "",
    response_model=list[TeachingAssignmentResponse],
)
def get_teaching_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    assignments = db.scalars(
        select(TeachingAssignment).order_by(
            TeachingAssignment.id
        )
    ).all()

    return assignments


@router.get(
    "/{assignment_id}",
    response_model=TeachingAssignmentResponse,
)
def get_teaching_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    assignment = db.scalar(
        select(TeachingAssignment).where(
            TeachingAssignment.id == assignment_id
        )
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teaching assignment not found",
        )

    return assignment


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_teaching_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    assignment = db.scalar(
        select(TeachingAssignment).where(
            TeachingAssignment.id == assignment_id
        )
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teaching assignment not found",
        )

    db.delete(assignment)
    db.commit()

    return None
