from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.connection import get_db
from app.models.assessment import Assessment
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.student_score import StudentScore
from app.models.user import User
from app.schemas.student_score import (
    StudentScoreCreate,
    StudentScoreResponse,
    StudentScoreUpdate,
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
    current_user: User = Depends(require_admin),
):
    student = db.scalar(
        select(Student).where(Student.id == score_data.student_id)
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    assessment = db.scalar(
        select(Assessment).where(
            Assessment.id == score_data.assessment_id
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    # Check that the student is enrolled in the assessment's
    # class and academic session.
    enrollment = db.scalar(
        select(Enrollment).where(
            (Enrollment.student_id == score_data.student_id)
            & (Enrollment.class_id == assessment.class_id)
            & (
                Enrollment.academic_session_id
                == assessment.academic_session_id
            )
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Student is not enrolled in the class and "
                "academic session for this assessment"
            ),
        )

    if score_data.score > float(assessment.max_score):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Score cannot be greater than "
                f"{assessment.max_score}"
            ),
        )

    existing_score = db.scalar(
        select(StudentScore).where(
            (StudentScore.student_id == score_data.student_id)
            & (
                StudentScore.assessment_id
                == score_data.assessment_id
            )
        )
    )

    if existing_score:
        raise HTTPException(
            status_code=409,
            detail="Score already exists for this student and assessment",
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
            status_code=409,
            detail="Score already exists for this student and assessment",
        )

    db.refresh(student_score)

    return student_score


@router.get(
    "",
    response_model=list[StudentScoreResponse],
)
def get_student_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    scores = db.scalars(
        select(StudentScore).order_by(StudentScore.id)
    ).all()

    return scores


@router.get(
    "/{score_id}",
    response_model=StudentScoreResponse,
)
def get_student_score(
    score_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    student_score = db.scalar(
        select(StudentScore).where(
            StudentScore.id == score_id
        )
    )

    if student_score is None:
        raise HTTPException(
            status_code=404,
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
    current_user: User = Depends(require_admin),
):
    student_score = db.scalar(
        select(StudentScore).where(
            StudentScore.id == score_id
        )
    )

    if student_score is None:
        raise HTTPException(
            status_code=404,
            detail="Student score not found",
        )

    assessment = db.scalar(
        select(Assessment).where(
            Assessment.id == student_score.assessment_id
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found",
        )

    if score_data.score > float(assessment.max_score):
        raise HTTPException(
            status_code=400,
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
    current_user: User = Depends(require_admin),
):
    student_score = db.scalar(
        select(StudentScore).where(
            StudentScore.id == score_id
        )
    )

    if student_score is None:
        raise HTTPException(
            status_code=404,
            detail="Student score not found",
        )

    db.delete(student_score)
    db.commit()

    return None
