from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.connection import get_db
from app.models.assessment import Assessment
from app.models.academic_session import AcademicSession
from app.models.class_model import Class
from app.models.subject import Subject
from app.models.term import Term
from app.models.user import User
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentUpdate,
)


router = APIRouter(
    prefix="/api/assessments",
    tags=["Assessments"],
)


@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment(
    assessment_data: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Validate class
    class_ = db.scalar(
        select(Class).where(Class.id == assessment_data.class_id)
    )

    if class_ is None:
        raise HTTPException(
            status_code=404,
            detail="Class not found",
        )

    # Validate subject
    subject = db.scalar(
        select(Subject).where(Subject.id == assessment_data.subject_id)
    )

    if subject is None:
        raise HTTPException(
            status_code=404,
            detail="Subject not found",
        )

    # Validate academic session
    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == assessment_data.academic_session_id
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=404,
            detail="Academic session not found",
        )

    # Validate term
    term = db.scalar(
        select(Term).where(Term.id == assessment_data.term_id)
    )

    if term is None:
        raise HTTPException(
            status_code=404,
            detail="Term not found",
        )

    # Make sure term belongs to the selected academic session
    if term.academic_session_id != assessment_data.academic_session_id:
        raise HTTPException(
            status_code=400,
            detail="Term does not belong to the selected academic session",
        )

    # Check for duplicate assessment
    existing_assessment = db.scalar(
        select(Assessment).where(
            (Assessment.class_id == assessment_data.class_id)
            & (Assessment.subject_id == assessment_data.subject_id)
            & (
                Assessment.academic_session_id
                == assessment_data.academic_session_id
            )
            & (Assessment.term_id == assessment_data.term_id)
            & (
                Assessment.assessment_type
                == assessment_data.assessment_type
            )
            & (Assessment.sequence == assessment_data.sequence)
        )
    )

    if existing_assessment:
        raise HTTPException(
            status_code=409,
            detail="Assessment already exists",
        )

    assessment = Assessment(
        class_id=assessment_data.class_id,
        subject_id=assessment_data.subject_id,
        academic_session_id=assessment_data.academic_session_id,
        term_id=assessment_data.term_id,
        assessment_type=assessment_data.assessment_type,
        sequence=assessment_data.sequence,
        name=assessment_data.name,
        max_score=assessment_data.max_score,
    )

    db.add(assessment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Assessment already exists",
        )

    db.refresh(assessment)

    return assessment


@router.get(
    "",
    response_model=list[AssessmentResponse],
)
def get_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    assessments = db.scalars(
        select(Assessment).order_by(Assessment.id)
    ).all()

    return assessments


@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponse,
)
def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    assessment = db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    return assessment


@router.patch(
    "/{assessment_id}",
    response_model=AssessmentResponse,
)
def update_assessment(
    assessment_id: int,
    assessment_data: AssessmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    assessment = db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    update_data = assessment_data.model_dump(
        exclude_unset=True
    )

    if "name" in update_data:
        assessment.name = update_data["name"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Unable to update assessment",
        )

    db.refresh(assessment)

    return assessment


@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    assessment = db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    db.delete(assessment)
    db.commit()

    return None
