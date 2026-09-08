from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.assessment import Assessment
from app.models.class_model import Class
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.student_score import StudentScore
from app.models.subject import Subject
from app.models.user import User
from app.schemas.student_score import (
    StudentScoreCreate,
    StudentScoreResponse,
    StudentScoreUpdate,
)
from app.services.subscription_service import (
    require_active_term_subscription,
)
from app.services.result_publication_service import (
    require_result_unpublished,
)


router = APIRouter(
    prefix="/api/student-scores",
    tags=["Student Scores"],
)


@router.post(
    "",
    response_model=StudentScoreResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student_score(
    score_data: StudentScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    student = db.scalar(
        select(Student).where(
            Student.id == score_data.student_id,
            Student.school_id == current_user.school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

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
            Assessment.id == score_data.assessment_id,
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

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    require_result_unpublished(
        db=db,
        class_id=assessment.class_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    enrollment = db.scalar(
        select(Enrollment)
        .join(
            Student,
            Enrollment.student_id == Student.id,
        )
        .join(
            Class,
            Enrollment.class_id == Class.id,
        )
        .join(
            AcademicSession,
            Enrollment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Enrollment.student_id == score_data.student_id,
            Enrollment.class_id == assessment.class_id,
            Enrollment.academic_session_id
            == assessment.academic_session_id,
            Student.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Student is not enrolled in the class and "
                "academic session for this assessment"
            ),
        )

    if score_data.score > float(assessment.max_score):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Score cannot be greater than "
                f"{assessment.max_score}"
            ),
        )

    existing_score = db.scalar(
        select(StudentScore).where(
            StudentScore.student_id == score_data.student_id,
            StudentScore.assessment_id
            == score_data.assessment_id,
        )
    )

    if existing_score:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Score already exists for this "
                "student and assessment"
            ),
        )

    student_score = StudentScore(
        student_id=score_data.student_id,
        assessment_id=score_data.assessment_id,
        score=score_data.score,
    )

    db.add(student_score)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Score already exists for this "
                "student and assessment"
            ),
        )

    db.refresh(student_score)

    return student_score


@router.get(
    "",
    response_model=list[StudentScoreResponse],
)
def get_student_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    scores = db.scalars(
        select(StudentScore)
        .join(
            Student,
            StudentScore.student_id == Student.id,
        )
        .join(
            Assessment,
            StudentScore.assessment_id == Assessment.id,
        )
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
            Student.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
        .order_by(StudentScore.id)
    ).all()

    return scores


@router.get(
    "/{score_id}",
    response_model=StudentScoreResponse,
)
def get_student_score(
    score_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    student_score = db.scalar(
        select(StudentScore)
        .join(
            Student,
            StudentScore.student_id == Student.id,
        )
        .join(
            Assessment,
            StudentScore.assessment_id == Assessment.id,
        )
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
            StudentScore.id == score_id,
            Student.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if student_score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student score not found",
        )

    return student_score


@router.patch(
    "/{score_id}",
    response_model=StudentScoreResponse,
)
def update_student_score(
    score_id: int,
    score_data: StudentScoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    student_score = db.scalar(
        select(StudentScore)
        .join(
            Student,
            StudentScore.student_id == Student.id,
        )
        .join(
            Assessment,
            StudentScore.assessment_id == Assessment.id,
        )
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
            StudentScore.id == score_id,
            Student.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if student_score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student score not found",
        )

    assessment = db.scalar(
        select(Assessment).where(
            Assessment.id == student_score.assessment_id
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    require_result_unpublished(
        db=db,
        class_id=assessment.class_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    if score_data.score > float(assessment.max_score):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Score cannot be greater than "
                f"{assessment.max_score}"
            ),
        )

    student_score.score = score_data.score

    db.commit()
    db.refresh(student_score)

    return student_score


@router.delete(
    "/{score_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student_score(
    score_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    student_score = db.scalar(
        select(StudentScore)
        .join(
            Student,
            StudentScore.student_id == Student.id,
        )
        .join(
            Assessment,
            StudentScore.assessment_id == Assessment.id,
        )
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
            StudentScore.id == score_id,
            Student.school_id == current_user.school_id,
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if student_score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student score not found",
        )

    assessment = db.scalar(
        select(Assessment).where(
            Assessment.id == student_score.assessment_id
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )

    require_active_term_subscription(
        db=db,
        school_id=current_user.school_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    require_result_unpublished(
        db=db,
        class_id=assessment.class_id,
        academic_session_id=assessment.academic_session_id,
        term_id=assessment.term_id,
    )

    db.delete(student_score)
    db.commit()

    return None
