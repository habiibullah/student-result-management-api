from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.connection import get_db
from app.models import AcademicSession, Term, User
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
    current_user: User = Depends(require_admin),
):
    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == term_data.academic_session_id
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    existing_term = db.scalar(
        select(Term).where(
            (Term.academic_session_id == term_data.academic_session_id)
            & (Term.name == term_data.name)
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
    current_user: User = Depends(require_admin),
):
    terms = db.scalars(
        select(Term).order_by(Term.id)
    ).all()

    return terms


@router.get(
    "/{term_id}",
    response_model=TermResponse,
)
def get_term(
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    term = db.scalar(
        select(Term).where(Term.id == term_id)
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
    current_user: User = Depends(require_admin),
):
    term = db.scalar(
        select(Term).where(Term.id == term_id)
    )

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found",
        )

    update_data = term_data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing_term = db.scalar(
            select(Term).where(
                (Term.academic_session_id == term.academic_session_id)
                & (Term.name == update_data["name"])
                & (Term.id != term_id)
            )
        )

        if existing_term:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Term already exists for this academic session",
            )

        term.name = update_data["name"]

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


@router.delete(
    "/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_term(
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    term = db.scalar(
        select(Term).where(Term.id == term_id)
    )

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found",
        )

    db.delete(term)
    db.commit()

    return None
