from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.assessment import Assessment
from app.models.class_model import Class
from app.models.enrollment import Enrollment
from app.models.grading_scale import GradingScale
from app.models.student import Student
from app.models.student_score import StudentScore
from app.models.subject import Subject
from app.models.term import Term
from app.models.user import User
from app.schemas.analytics import (
    ClassAnalyticsResponse,
    SubjectAnalyticsItem,
)
from app.services.result_service import (
    calculate_class_statistics,
    calculate_subject_statistics,
    compute_student_term_result,
)


router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"],
)


@router.get(
    "/classes/{class_id}",
    response_model=ClassAnalyticsResponse,
)
def get_class_analytics(
    class_id: int,
    academic_session_id: int,
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    school_id = current_user.school_id

    class_record = db.scalar(
        select(Class).where(
            Class.id == class_id,
            Class.school_id == school_id,
        )
    )

    if class_record is None:
        raise HTTPException(
            status_code=404,
            detail="Class not found",
        )

    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == academic_session_id,
            AcademicSession.school_id == school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=404,
            detail="Academic session not found",
        )

    term = db.scalar(
        select(Term).where(
            Term.id == term_id,
        )
    )

    if term is None:
        raise HTTPException(
            status_code=404,
            detail="Term not found",
        )

    if term.academic_session_id != academic_session_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "Term does not belong to the selected "
                "academic session"
            ),
        )

    enrollments = db.scalars(
        select(Enrollment)
        .join(
            Student,
            Enrollment.student_id == Student.id,
        )
        .where(
            Enrollment.class_id == class_id,
            Enrollment.academic_session_id
            == academic_session_id,
            Student.school_id == school_id,
        )
        .order_by(Enrollment.id)
    ).all()

    student_ids = [
        enrollment.student_id
        for enrollment in enrollments
    ]

    assessments = db.scalars(
        select(Assessment).where(
            Assessment.class_id == class_id,
            Assessment.academic_session_id
            == academic_session_id,
            Assessment.term_id == term_id,
        )
    ).all()

    assessment_ids = [
        assessment.id
        for assessment in assessments
    ]

    subject_ids = list(
        {
            assessment.subject_id
            for assessment in assessments
        }
    )

    subjects = []

    if subject_ids:
        subjects = db.scalars(
            select(Subject).where(
                Subject.id.in_(subject_ids),
                Subject.school_id == school_id,
            )
        ).all()

    subjects_by_id = {
        subject.id: subject
        for subject in subjects
    }

    scores_by_key = {}

    if assessment_ids and student_ids:
        scores = db.scalars(
            select(StudentScore).where(
                StudentScore.assessment_id.in_(
                    assessment_ids
                ),
                StudentScore.student_id.in_(
                    student_ids
                ),
            )
        ).all()

        scores_by_key = {
            (
                score.student_id,
                score.assessment_id,
            ): float(score.score)
            for score in scores
        }

    grading_scales = db.scalars(
        select(GradingScale)
        .where(
            GradingScale.school_id == school_id
        )
        .order_by(
            GradingScale.minimum_score.desc()
        )
    ).all()

    student_results = {}

    for enrollment in enrollments:
        student_results[enrollment.student_id] = (
            compute_student_term_result(
                student_id=enrollment.student_id,
                assessments=assessments,
                subjects_by_id=subjects_by_id,
                scores_by_key=scores_by_key,
                grading_scales=grading_scales,
            )
        )

    class_statistics = calculate_class_statistics(
        student_results
    )

    subject_statistics = calculate_subject_statistics(
        student_results
    )

    complete_results = sum(
        1
        for result in student_results.values()
        if result["result_status"] == "COMPLETE"
    )

    subject_items = []

    for subject in subjects:
        statistics = subject_statistics.get(
            subject.id,
            {
                "class_average": None,
                "positions": {},
            },
        )

        subject_items.append(
            SubjectAnalyticsItem(
                subject_id=subject.id,
                subject_name=subject.name,
                class_average=statistics[
                    "class_average"
                ],
                completed_students=len(
                    statistics["positions"]
                ),
            )
        )

    return ClassAnalyticsResponse(
        class_id=class_record.id,
        class_name=class_record.name,
        academic_session_id=academic_session_id,
        term_id=term_id,
        enrolled_students=len(enrollments),
        complete_results=complete_results,
        incomplete_results=(
            len(enrollments) - complete_results
        ),
        highest_average=class_statistics[
            "highest_average"
        ],
        lowest_average=class_statistics[
            "lowest_average"
        ],
        class_average=class_statistics[
            "class_average"
        ],
        subjects=subject_items,
    )