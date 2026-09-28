from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models import (
    AcademicSession,
    Class,
    ClassSubject,
    Subject,
    User,
)
from app.schemas.class_subject import (
    ClassSubjectBulkCreate,
    ClassSubjectCreate,
    ClassSubjectResponse,
)


router = APIRouter(
    prefix="/api/class-subjects",
    tags=["Class Subjects"],
)


def _validate_class(
    db: Session,
    class_id: int,
    school_id: int,
) -> Class:
    class_ = db.scalar(
        select(Class).where(
            Class.id == class_id,
            Class.school_id == school_id,
        )
    )

    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    return class_


def _validate_academic_session(
    db: Session,
    academic_session_id: int,
    school_id: int,
) -> AcademicSession:
    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == academic_session_id,
            AcademicSession.school_id == school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    return academic_session


def _validate_subject(
    db: Session,
    subject_id: int,
    school_id: int,
) -> Subject:
    subject = db.scalar(
        select(Subject).where(
            Subject.id == subject_id,
            Subject.school_id == school_id,
        )
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    return subject


@router.post(
    "",
    response_model=ClassSubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class_subject(
    assignment_data: ClassSubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    _validate_class(
        db,
        assignment_data.class_id,
        current_user.school_id,
    )
    _validate_subject(
        db,
        assignment_data.subject_id,
        current_user.school_id,
    )
    _validate_academic_session(
        db,
        assignment_data.academic_session_id,
        current_user.school_id,
    )

    existing_assignment = db.scalar(
        select(ClassSubject).where(
            ClassSubject.class_id == assignment_data.class_id,
            ClassSubject.subject_id == assignment_data.subject_id,
            ClassSubject.academic_session_id
            == assignment_data.academic_session_id,
        )
    )

    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This class-subject assignment already exists",
        )

    assignment = ClassSubject(
        class_id=assignment_data.class_id,
        subject_id=assignment_data.subject_id,
        academic_session_id=assignment_data.academic_session_id,
    )

    db.add(assignment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This class-subject assignment already exists",
        )

    db.refresh(assignment)

    return assignment


@router.post(
    "/bulk",
    response_model=list[ClassSubjectResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_class_subjects_bulk(
    assignment_data: ClassSubjectBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    _validate_class(
        db,
        assignment_data.class_id,
        current_user.school_id,
    )
    _validate_academic_session(
        db,
        assignment_data.academic_session_id,
        current_user.school_id,
    )

    subjects = db.scalars(
        select(Subject).where(
            Subject.id.in_(assignment_data.subject_ids),
            Subject.school_id == current_user.school_id,
        )
    ).all()

    found_subject_ids = {subject.id for subject in subjects}
    requested_subject_ids = set(assignment_data.subject_ids)

    if found_subject_ids != requested_subject_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more subjects were not found",
        )

    existing_subject_ids = set(
        db.scalars(
            select(ClassSubject.subject_id).where(
                ClassSubject.class_id == assignment_data.class_id,
                ClassSubject.academic_session_id
                == assignment_data.academic_session_id,
                ClassSubject.subject_id.in_(assignment_data.subject_ids),
            )
        ).all()
    )

    if existing_subject_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more class-subject assignments already exist",
        )

    assignments = [
        ClassSubject(
            class_id=assignment_data.class_id,
            subject_id=subject_id,
            academic_session_id=assignment_data.academic_session_id,
        )
        for subject_id in assignment_data.subject_ids
    ]

    db.add_all(assignments)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more class-subject assignments already exist",
        )

    for assignment in assignments:
        db.refresh(assignment)

    return assignments


@router.get(
    "",
    response_model=list[ClassSubjectResponse],
)
def get_class_subjects(
    class_id: int | None = Query(default=None, gt=0),
    academic_session_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    query = (
        select(ClassSubject)
        .join(
            Class,
            ClassSubject.class_id == Class.id,
        )
        .join(
            Subject,
            ClassSubject.subject_id == Subject.id,
        )
        .join(
            AcademicSession,
            ClassSubject.academic_session_id == AcademicSession.id,
        )
        .where(
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if class_id is not None:
        query = query.where(
            ClassSubject.class_id == class_id
        )

    if academic_session_id is not None:
        query = query.where(
            ClassSubject.academic_session_id
            == academic_session_id
        )

    assignments = db.scalars(
        query.order_by(
            ClassSubject.class_id,
            ClassSubject.subject_id,
        )
    ).all()

    return assignments


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_class_subject(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    assignment = db.scalar(
        select(ClassSubject)
        .join(
            Class,
            ClassSubject.class_id == Class.id,
        )
        .join(
            Subject,
            ClassSubject.subject_id == Subject.id,
        )
        .join(
            AcademicSession,
            ClassSubject.academic_session_id == AcademicSession.id,
        )
        .where(
            ClassSubject.id == assignment_id,
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class-subject assignment not found",
        )

    db.delete(assignment)
    db.commit()

    return None
