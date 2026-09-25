from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.student import Student
from app.models.student_behavioural_assessment import (
    StudentBehaviouralAssessment,
)
from app.models.term import Term
from app.models.user import User
from app.schemas.student_behavioural_assessment import (
    StudentBehaviouralAssessmentCreate,
    StudentBehaviouralAssessmentResponse,
    StudentBehaviouralAssessmentUpdate,
)
from app.services.result_publication_service import (
    require_student_result_unpublished,
)
from app.services.subscription_service import (
    require_active_term_subscription,
)


router = APIRouter(
    prefix="/api/student-behavioural-assessments",
    tags=["Student Behavioural Assessments"],
)


@router.post(
    "",
    response_model=StudentBehaviouralAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student_behavioural_assessment(
    assessment_data: StudentBehaviouralAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    student = db.scalar(
        select(Student).where(
            Student.id == assessment_data.student_id,
            Student.school_id == current_user.school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

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

    term = db.scalar(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id == AcademicSession.id,
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

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=assessment_data.academic_session_id,
        term_id=assessment_data.term_id,
    )

    require_student_result_unpublished(
        db=db,
        student_id=assessment_data.student_id,
        academic_session_id=assessment_data.academic_session_id,
        term_id=assessment_data.term_id,
    )

    existing_assessment = db.scalar(
        select(StudentBehaviouralAssessment).where(
            StudentBehaviouralAssessment.student_id
            == assessment_data.student_id,
            StudentBehaviouralAssessment.academic_session_id
            == assessment_data.academic_session_id,
            StudentBehaviouralAssessment.term_id
            == assessment_data.term_id,
        )
    )

    if existing_assessment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Behavioural assessment already exists for "
                "this student, session and term"
            ),
        )

    assessment = StudentBehaviouralAssessment(
        **assessment_data.model_dump()
    )

    db.add(assessment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Behavioural assessment already exists for "
                "this student, session and term"
            ),
        )

    db.refresh(assessment)

    return assessment


@router.get(
    "",
    response_model=list[StudentBehaviouralAssessmentResponse],
)
def get_student_behavioural_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    assessments = db.scalars(
        select(StudentBehaviouralAssessment)
        .join(
            Student,
            StudentBehaviouralAssessment.student_id == Student.id,
        )
        .join(
            AcademicSession,
            StudentBehaviouralAssessment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Student.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
        .order_by(StudentBehaviouralAssessment.id)
    ).all()

    return assessments


@router.get(
    "/{assessment_id}",
    response_model=StudentBehaviouralAssessmentResponse,
)
def get_student_behavioural_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    assessment = db.scalar(
        select(StudentBehaviouralAssessment)
        .join(
            Student,
            StudentBehaviouralAssessment.student_id == Student.id,
        )
        .join(
            AcademicSession,
            StudentBehaviouralAssessment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            StudentBehaviouralAssessment.id == assessment_id,
            Student.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Behavioural assessment not found",
        )

    return assessment


@router.patch(
    "/{assessment_id}",
    response_model=StudentBehaviouralAssessmentResponse,
)
def update_student_behavioural_assessment(
    assessment_id: int,
    assessment_data: StudentBehaviouralAssessmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    assessment = db.scalar(
        select(StudentBehaviouralAssessment)
        .join(
            Student,
            StudentBehaviouralAssessment.student_id == Student.id,
        )
        .join(
            AcademicSession,
            StudentBehaviouralAssessment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            StudentBehaviouralAssessment.id == assessment_id,
            Student.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Behavioural assessment not found",
        )

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    require_student_result_unpublished(
        db=db,
        student_id=assessment.student_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    update_data = assessment_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(assessment, field, value)

    db.commit()
    db.refresh(assessment)

    return assessment


@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student_behavioural_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    assessment = db.scalar(
        select(StudentBehaviouralAssessment)
        .join(
            Student,
            StudentBehaviouralAssessment.student_id == Student.id,
        )
        .join(
            AcademicSession,
            StudentBehaviouralAssessment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            StudentBehaviouralAssessment.id == assessment_id,
            Student.school_id == current_user.school_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Behavioural assessment not found",
        )

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    require_student_result_unpublished(
        db=db,
        student_id=assessment.student_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    db.delete(assessment)
    db.commit()

    return None
