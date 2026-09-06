from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.database.connection import get_db
from app.models.assessment import Assessment
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.student_score import StudentScore
from app.models.user import User
from app.schemas.result import ResultResponse


router = APIRouter(
    prefix="/api/results",
    tags=["Results"],
)


def calculate_grade(total: float) -> str:
    if total >= 70:
        return "A"
    elif total >= 60:
        return "B"
    elif total >= 50:
        return "C"
    elif total >= 45:
        return "D"
    elif total >= 40:
        return "E"
    return "F"


@router.get(
    "/student/{student_id}",
    response_model=ResultResponse,
)
def get_student_result(
    student_id: int,
    subject_id: int = Query(gt=0),
    term_id: int = Query(gt=0),
    academic_session_id: int = Query(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    student = db.scalar(
        select(Student).where(Student.id == student_id)
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    enrollment = db.scalar(
        select(Enrollment).where(
            (Enrollment.student_id == student_id)
            & (
                Enrollment.academic_session_id
                == academic_session_id
            )
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=404,
            detail="Student enrollment not found for this academic session",
        )

    assessments = db.scalars(
        select(Assessment).where(
            (Assessment.class_id == enrollment.class_id)
            & (Assessment.subject_id == subject_id)
            & (
                Assessment.academic_session_id
                == academic_session_id
            )
            & (Assessment.term_id == term_id)
        )
    ).all()

    if not assessments:
        raise HTTPException(
            status_code=404,
            detail="No assessments found for this result",
        )

    assessment_ids = [
        assessment.id
        for assessment in assessments
    ]

    scores = db.scalars(
        select(StudentScore).where(
            (StudentScore.student_id == student_id)
            & (
                StudentScore.assessment_id.in_(
                    assessment_ids
                )
            )
        )
    ).all()

    score_by_assessment = {
        score.assessment_id: float(score.score)
        for score in scores
    }

    ca1 = 0.0
    ca2 = 0.0
    ca3 = 0.0
    exam = 0.0

    for assessment in assessments:
        score = score_by_assessment.get(
            assessment.id,
            0.0,
        )

        if (
            assessment.assessment_type == "CA"
            and assessment.sequence == 1
        ):
            ca1 = score

        elif (
            assessment.assessment_type == "CA"
            and assessment.sequence == 2
        ):
            ca2 = score

        elif (
            assessment.assessment_type == "CA"
            and assessment.sequence == 3
        ):
            ca3 = score

        elif assessment.assessment_type == "EXAM":
            exam = score

    total = ca1 + ca2 + ca3 + exam

    percentage = total

    grade = calculate_grade(total)

    return ResultResponse(
        student_id=student_id,
        subject_id=subject_id,
        class_id=enrollment.class_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        ca1=ca1,
        ca2=ca2,
        ca3=ca3,
        exam=exam,
        total=total,
        percentage=percentage,
        grade=grade,
    )
