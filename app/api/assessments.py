from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.assessment import Assessment
from app.models.class_model import Class
from app.models.subject import Subject
from app.models.term import Term
from app.models.user import User
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentUpdate,
)
from app.services.result_publication_service import (
    require_result_unpublished,
)
from app.services.subscription_service import (
    require_active_term_subscription,
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
    current_user: User = Depends(require_school_admin),
):
    # Validate class belongs to authenticated school.
    class_ = db.scalar(
        select(Class).where(
            Class.id == assessment_data.class_id,
            Class.school_id == current_user.school_id,
        )
    )

    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    # Validate subject belongs to authenticated school.
    subject = db.scalar(
        select(Subject).where(
            Subject.id == assessment_data.subject_id,
            Subject.school_id == current_user.school_id,
        )
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    # Validate academic session belongs to authenticated school.
    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id
            == assessment_data.academic_session_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    # Validate term through its school-owned academic session.
    term = db.scalar(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Term.id == assessment_data.term_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found",
        )

    # Term must belong to the selected academic session.
    if (
        term.academic_session_id
        != assessment_data.academic_session_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Term does not belong to the selected "
                "academic session"
            ),
        )

    # Require an active subscription for this exact term.
    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=(
            assessment_data.academic_session_id
        ),
        term_id=assessment_data.term_id,
    )

    # Published results must remain locked.
    require_result_unpublished(
        db=db,
        class_id=assessment_data.class_id,
        academic_session_id=(
            assessment_data.academic_session_id
        ),
        term_id=assessment_data.term_id,
    )

    existing_assessment = db.scalar(
        select(Assessment).where(
            Assessment.class_id
            == assessment_data.class_id,
            Assessment.subject_id
            == assessment_data.subject_id,
            Assessment.academic_session_id
            == assessment_data.academic_session_id,
            Assessment.term_id
            == assessment_data.term_id,
            Assessment.assessment_type
            == assessment_data.assessment_type,
            Assessment.sequence
            == assessment_data.sequence,
        )
    )

    if existing_assessment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment already exists",
        )

    assessment = Assessment(
        class_id=assessment_data.class_id,
        subject_id=assessment_data.subject_id,
        academic_session_id=(
            assessment_data.academic_session_id
        ),
        term_id=assessment_data.term_id,
        assessment_type=(
            assessment_data.assessment_type
        ),
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
            status_code=status.HTTP_409_CONFLICT,
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
    current_user: User = Depends(require_school_admin),
):
    assessments = db.scalars(
        select(Assessment)
        .join(
            Class,
            Assessment.class_id == Class.id,
        )
        .join(
            Subject,
            Assessment.subject_id == Subject.id,
        )
        .join(
            AcademicSession,
            Assessment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
        .order_by(Assessment.id)
    ).all()

    return assessments


@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponse,
)
def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    assessment = db.scalar(
        select(Assessment)
        .join(
            Class,
            Assessment.class_id == Class.id,
        )
        .join(
            Subject,
            Assessment.subject_id == Subject.id,
        )
        .join(
            AcademicSession,
            Assessment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Assessment.id == assessment_id,
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
    current_user: User = Depends(require_school_admin),
):
    assessment = db.scalar(
        select(Assessment)
        .join(
            Class,
            Assessment.class_id == Class.id,
        )
        .join(
            Subject,
            Assessment.subject_id == Subject.id,
        )
        .join(
            AcademicSession,
            Assessment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Assessment.id == assessment_id,
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    # Subscription must still be active before academic
    # records for this term can be changed.
    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=(
            assessment.academic_session_id
        ),
        term_id=assessment.term_id,
    )

    require_result_unpublished(
        db=db,
        class_id=assessment.class_id,
        academic_session_id=(
            assessment.academic_session_id
        ),
        term_id=assessment.term_id,
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
            status_code=status.HTTP_409_CONFLICT,
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
    current_user: User = Depends(require_school_admin),
):
    assessment = db.scalar(
        select(Assessment)
        .join(
            Class,
            Assessment.class_id == Class.id,
        )
        .join(
            Subject,
            Assessment.subject_id == Subject.id,
        )
        .join(
            AcademicSession,
            Assessment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Assessment.id == assessment_id,
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    # Subscription must remain active before deleting
    # academic records belonging to this term.
    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=(
            assessment.academic_session_id
        ),
        term_id=assessment.term_id,
    )

    require_result_unpublished(
        db=db,
        class_id=assessment.class_id,
        academic_session_id=(
            assessment.academic_session_id
        ),
        term_id=assessment.term_id,
    )

    db.delete(assessment)
    db.commit()

    return None
