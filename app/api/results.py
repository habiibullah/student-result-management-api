from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
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
from app.models.term import Term
from app.models.user import User
from app.schemas.result import ResultResponse
from app.services.result_service import calculate_grade


router = APIRouter(
    prefix="/api/results",
    tags=["Results"],
)


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
    current_user: User = Depends(require_school_admin),
):
    # Student must belong to authenticated school.
    student = db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.school_id == current_user.school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Academic session must belong to authenticated school.
    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id == academic_session_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    # Subject must belong to authenticated school.
    subject = db.scalar(
        select(Subject).where(
            Subject.id == subject_id,
            Subject.school_id == current_user.school_id,
        )
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    # Term must belong to the selected academic session
    # and authenticated school.
    term = db.scalar(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id == AcademicSession.id,
        )
        .where(
            Term.id == term_id,
            Term.academic_session_id == academic_session_id,
            AcademicSession.school_id == current_user.school_id,
        )
    )

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found",
        )

    # Enrollment must connect this student to a class
    # belonging to the authenticated school.
    enrollment = db.scalar(
        select(Enrollment)
        .join(
            Class,
            Enrollment.class_id == Class.id,
        )
        .where(
            Enrollment.student_id == student_id,
            Enrollment.academic_session_id == academic_session_id,
            Class.school_id == current_user.school_id,
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Student enrollment not found for this "
                "academic session"
            ),
        )

    # Assessments must belong to the student's enrolled class,
    # selected subject/session/term, and authenticated school.
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
            Assessment.class_id == enrollment.class_id,
            Assessment.subject_id == subject_id,
            Assessment.academic_session_id
            == academic_session_id,
            Assessment.term_id == term_id,
            Class.school_id == current_user.school_id,
            Subject.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
        .order_by(
            Assessment.assessment_type,
            Assessment.sequence,
        )
    ).all()

    if not assessments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessments found for this result",
        )

    assessment_ids = [
        assessment.id
        for assessment in assessments
    ]

    scores = db.scalars(
        select(StudentScore).where(
            StudentScore.student_id == student_id,
            StudentScore.assessment_id.in_(
                assessment_ids
            ),
        )
    ).all()

    score_by_assessment = {
        score.assessment_id: float(score.score)
        for score in scores
    }

    ca1 = None
    ca2 = None
    ca3 = None
    exam = None

    for assessment in assessments:
        score = score_by_assessment.get(
            assessment.id
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

    is_complete = all(
        value is not None
        for value in [ca1, ca2, ca3, exam]
    )

    if is_complete:
        total = ca1 + ca2 + ca3 + exam
        percentage = total
        grade = calculate_grade(total)
        result_status = "COMPLETE"
    else:
        total = None
        percentage = None
        grade = None
        result_status = "INCOMPLETE"

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
        status=result_status,
    )
