from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_school_admin,
)
from app.database.connection import get_db
from app.models import (
    Assessment,
    Subject,
    TeachingAssignment,
    User,
)
from app.schemas.subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)


router = APIRouter(
    prefix="/api/subjects",
    tags=["Subjects"],
)


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    subject_data: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    existing_subject = db.scalar(
        select(Subject).where(
            Subject.school_id == current_user.school_id,
            (
                (Subject.name == subject_data.name)
                | (Subject.code == subject_data.code)
            ),
        )
    )

    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Subject with this name or code "
                "already exists in this school"
            ),
        )

    subject = Subject(
        school_id=current_user.school_id,
        name=subject_data.name,
        code=subject_data.code,
        description=subject_data.description,
    )

    db.add(subject)
    db.commit()
    db.refresh(subject)

    return subject


@router.get(
    "",
    response_model=list[SubjectResponse],
)
def get_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    subjects = db.scalars(
        select(Subject)
        .where(
            Subject.school_id == current_user.school_id
        )
        .order_by(Subject.name)
    ).all()

    return subjects


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )

    subject = db.scalar(
        select(Subject).where(
            Subject.id == subject_id,
            Subject.school_id == current_user.school_id,
        )
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    return subject


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def update_subject(
    subject_id: int,
    subject_data: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    subject = db.scalar(
        select(Subject).where(
            Subject.id == subject_id,
            Subject.school_id == current_user.school_id,
        )
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    if subject_data.name is not None:
        existing_subject = db.scalar(
            select(Subject).where(
                Subject.school_id == current_user.school_id,
                Subject.name == subject_data.name,
                Subject.id != subject_id,
            )
        )

        if existing_subject:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Subject with this name "
                    "already exists in this school"
                ),
            )

        subject.name = subject_data.name

    if subject_data.code is not None:
        existing_subject = db.scalar(
            select(Subject).where(
                Subject.school_id == current_user.school_id,
                Subject.code == subject_data.code,
                Subject.id != subject_id,
            )
        )

        if existing_subject:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Subject with this code "
                    "already exists in this school"
                ),
            )

        subject.code = subject_data.code

    if subject_data.description is not None:
        subject.description = subject_data.description

    db.commit()
    db.refresh(subject)

    return subject


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    subject = db.scalar(
        select(Subject).where(
            Subject.id == subject_id,
            Subject.school_id == current_user.school_id,
        )
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    assignment_count = db.scalar(
        select(func.count(TeachingAssignment.id)).where(
            TeachingAssignment.subject_id == subject.id
        )
    )


    assessment_count = db.scalar(
        select(func.count(Assessment.id)).where(
            Assessment.subject_id == subject.id
        )
    )

    if assignment_count > 0 or assessment_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Subject cannot be deleted because it already has "
                "academic records or teaching assignments."
        ),
    )

    db.delete(subject)
    db.commit()

    return None
