from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.class_model import Class
from app.models.enrollment import Enrollment
from app.models.published_report_snapshot import (
    PublishedReportSnapshot,
)
from app.models.result_publication import ResultPublication
from app.models.user import User
from app.schemas.report_sheet import (
    ClassReportSummaryItem,
    StudentReportSheetResponse,
)
from app.services.report_sheet_service import (
    build_student_report_sheet,
)
from app.models.student import Student

from app.models.assessment import Assessment
from app.models.grading_scale import GradingScale
from app.models.student_score import StudentScore
from app.models.subject import Subject
from app.models.term import Term

from app.services.result_service import (
    compute_student_term_result,
)


router = APIRouter(
    prefix="/api/report-sheets",
    tags=["Report Sheets"],
)

@router.get(
    "/class-summary",
    response_model=list[ClassReportSummaryItem],
)
def get_class_report_summary(
    class_id: int,
    academic_session_id: int,
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    school_id = current_user.school_id

    # Validate class ownership.
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

    # Validate academic session ownership.
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

    # Validate term and session relationship.
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

    # Get students enrolled in this class/session.
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

    if not enrollments:
        return []

    student_ids = [
        enrollment.student_id
        for enrollment in enrollments
    ]

    students = db.scalars(
        select(Student).where(
            Student.id.in_(student_ids),
            Student.school_id == school_id,
        )
    ).all()

    students_by_id = {
        student.id: student
        for student in students
    }

    # Load the class assessments once.
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

    # Load all relevant scores once.
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

    summary = []

    for enrollment in enrollments:
        student = students_by_id.get(
            enrollment.student_id
        )

        if student is None:
            continue

        computed = compute_student_term_result(
            student_id=student.id,
            assessments=assessments,
            subjects_by_id=subjects_by_id,
            scores_by_key=scores_by_key,
            grading_scales=grading_scales,
        )

        summary.append(
            ClassReportSummaryItem(
                student_id=student.id,
                admission_number=student.admission_number,
                student_name=(
                    f"{student.first_name} "
                    f"{student.last_name}"
                ).strip(),
                result_status=computed[
                    "result_status"
                ],
                number_of_subjects=computed[
                    "number_of_subjects"
                ],
                completed_subjects=computed[
                    "completed_subjects"
                ],
                average=computed["average"],
                overall_grade=computed[
                    "overall_grade"
                ],
            )
        )

    return summary


@router.get(
    "/student/{student_id}",
    response_model=StudentReportSheetResponse,
)
def get_student_report_sheet(
    student_id: int,
    academic_session_id: int,
    term_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    enrollment = db.scalar(
        select(Enrollment)
        .join(
            Student,
            Enrollment.student_id == Student.id,
        )
        .join(
            AcademicSession,
            Enrollment.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Enrollment.student_id == student_id,
            Enrollment.academic_session_id
            == academic_session_id,
            Student.school_id == current_user.school_id,
            AcademicSession.school_id
            == current_user.school_id,
        )
    )

    if enrollment is not None:
        publication = db.scalar(
            select(ResultPublication)
            .join(
                Class,
                ResultPublication.class_id == Class.id,
            )
            .join(
                AcademicSession,
                ResultPublication.academic_session_id
                == AcademicSession.id,
            )
            .where(
                ResultPublication.class_id
                == enrollment.class_id,
                ResultPublication.academic_session_id
                == academic_session_id,
                ResultPublication.term_id == term_id,
                ResultPublication.status == "published",
                Class.school_id == current_user.school_id,
                AcademicSession.school_id
                == current_user.school_id,
            )
        )

        if publication is not None:
            snapshot = db.scalar(
                select(PublishedReportSnapshot).where(
                    PublishedReportSnapshot.publication_id
                    == publication.id,
                    PublishedReportSnapshot.student_id
                    == student_id,
                )
            )

            if snapshot is not None:
                return StudentReportSheetResponse.model_validate(
                    snapshot.report_data
                )

    return build_student_report_sheet(
        db=db,
        school_id=current_user.school_id,
        student_id=student_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
    )
