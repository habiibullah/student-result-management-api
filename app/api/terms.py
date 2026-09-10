from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models import (
    AcademicSession,
    Assessment,
    ResultPublication,
    StudentAttendance,
    Subscription,
    Term,
    TermReportComment,
    User,
)
from app.schemas.term import (
    TermCreate,
    TermResponse,
    TermUpdate,
)

router = APIRouter(
    prefix="/api/terms",
    tags=["Terms"],
)


@router.post(
    "",
    response_model=TermResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_term(
    term_data: TermCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    # Verify that the academic session belongs
    # to the authenticated school.
    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id
            == term_data.academic_session_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    existing_term = db.scalar(
        select(Term).where(
            Term.academic_session_id
            == term_data.academic_session_id,
            Term.name == term_data.name,
        )
    )

    if existing_term:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Term already exists for this academic session",
        )

    term = Term(
        academic_session_id=term_data.academic_session_id,
        name=term_data.name,
        closing_date=term_data.closing_date,
        next_term_resumption_date=(
            term_data.next_term_resumption_date
        ),
    )

    db.add(term)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Term already exists for this academic session",
        )

    db.refresh(term)

    return term


@router.get(
    "",
    response_model=list[TermResponse],
)
def get_terms(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    terms = db.scalars(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id
            == AcademicSession.id,
        )
        .where(
            AcademicSession.school_id
            == current_user.school_id
        )
        .order_by(Term.id)
    ).all()

    return terms


@router.get(
    "/{term_id}",
    response_model=TermResponse,
)
def get_term(
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    term = db.scalar(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Term.id == term_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found",
        )

    return term


@router.patch(
    "/{term_id}",
    response_model=TermResponse,
)
def update_term(
    term_id: int,
    term_data: TermUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    term = db.scalar(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Term.id == term_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found",
        )

    update_data = term_data.model_dump(
        exclude_unset=True
    )

    if "closing_date" in update_data:
        term.closing_date = update_data[
            "closing_date"
        ]

    if "next_term_resumption_date" in update_data:
        term.next_term_resumption_date = (
            update_data[
                "next_term_resumption_date"
            ]
        )

    if "name" in update_data:
        existing_term = db.scalar(
            select(Term).where(
                Term.academic_session_id
                == term.academic_session_id,
                Term.name
                == update_data["name"],
                Term.id != term_id,
            )
        )

        if existing_term:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Term already exists for "
                    "this academic session"
                ),
            )

        term.name = update_data["name"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Term already exists for "
                "this academic session"
            ),
        )

    db.refresh(term)

    return term


@router.delete(
    "/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_term(
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    term = db.scalar(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Term.id == term_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found",
        )

    assessment_count = db.scalar(
        select(func.count(Assessment.id)).where(
            Assessment.term_id == term.id
        )
    )

    attendance_count = db.scalar(
        select(func.count(StudentAttendance.id)).where(
            StudentAttendance.term_id == term.id
        )
    )

    comment_count = db.scalar(
        select(func.count(TermReportComment.id)).where(
            TermReportComment.term_id == term.id
        )
    )

    subscription_count = db.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.term_id == term.id
        )
    )

    publication_count = db.scalar(
        select(func.count(ResultPublication.id)).where(
            ResultPublication.term_id == term.id
        )
    )

    if (
        assessment_count > 0
        or attendance_count > 0
        or comment_count > 0
        or subscription_count > 0
        or publication_count > 0
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Term cannot be deleted because it already has "
                "academic records or related data."
            ),
        )

    db.delete(term)
    db.commit()

    return None
