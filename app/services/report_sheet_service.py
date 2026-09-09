from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic_session import AcademicSession
from app.models.assessment import Assessment
from app.models.class_model import Class
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.student_attendance import StudentAttendance
from app.models.student_score import StudentScore
from app.models.subject import Subject
from app.models.term import Term
from app.models.term_report_comment import TermReportComment
from app.models.school import School


from app.schemas.report_sheet import (
    ReportSheetAttendance,
    ReportSheetClass,
    ReportSheetComments,
    ReportSheetPerformanceSummary,
    ReportSheetStudent,
    ReportSheetTerm,
    StudentReportSheetResponse,
    ReportSheetSchool,
)

from app.services.result_service import (
    calculate_class_positions,
    compute_student_term_result,
)


def build_student_report_sheet(
    db: Session,
    school_id: int,
    student_id: int,
    academic_session_id: int,
    term_id: int,
) -> StudentReportSheetResponse:

    # ---------------------------------------------------------
    # 1. GET STUDENT
    # ---------------------------------------------------------

    student = db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.school_id == school_id,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    # ---------------------------------------------------------
    # GET SCHOOL
    # ---------------------------------------------------------

    school = db.scalar(
        select(School).where(
            School.id == school_id,
        )
    )

    if school is None:
        raise HTTPException(
            status_code=404,
            detail="School not found",
        )

    # ---------------------------------------------------------
    # 2. GET STUDENT ENROLLMENT
    # ---------------------------------------------------------

    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.academic_session_id
            == academic_session_id,
        )
    )

    if enrollment is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Student enrollment not found for "
                "the selected academic session"
            ),
        )

    # ---------------------------------------------------------
    # 3. GET CLASS
    # ---------------------------------------------------------

    class_record = db.scalar(
        select(Class).where(
            Class.id == enrollment.class_id,
            Class.school_id == school_id,
        )
    )

    if class_record is None:
        raise HTTPException(
            status_code=404,
            detail="Class not found",
        )

    # ---------------------------------------------------------
    # 4. GET ACADEMIC SESSION
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 5. GET TERM
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 6. GET ASSESSMENTS
    # ---------------------------------------------------------

    assessments = db.scalars(
        select(Assessment).where(
            Assessment.class_id == enrollment.class_id,
            Assessment.academic_session_id
            == academic_session_id,
            Assessment.term_id == term_id,
        )
    ).all()

    assessment_ids = [
        assessment.id
        for assessment in assessments
    ]

    # ---------------------------------------------------------
    # 7. GET SUBJECTS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 8. GET ALL STUDENTS IN SAME CLASS
    # ---------------------------------------------------------

    class_enrollments = db.scalars(
        select(Enrollment).where(
            Enrollment.class_id == enrollment.class_id,
            Enrollment.academic_session_id
            == academic_session_id,
        )
    ).all()

    class_student_ids = [
        class_enrollment.student_id
        for class_enrollment in class_enrollments
    ]

    # ---------------------------------------------------------
    # 9. GET SCORES FOR THE CLASS
    # ---------------------------------------------------------

    scores = []

    if assessment_ids and class_student_ids:
        scores = db.scalars(
            select(StudentScore).where(
                StudentScore.assessment_id.in_(
                    assessment_ids
                ),
                StudentScore.student_id.in_(
                    class_student_ids
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

    # ---------------------------------------------------------
    # 10. COMPUTE RESULTS FOR ALL STUDENTS
    # ---------------------------------------------------------

    all_results = {}

    for class_enrollment in class_enrollments:
        result = compute_student_term_result(
            student_id=class_enrollment.student_id,
            assessments=assessments,
            subjects_by_id=subjects_by_id,
            scores_by_key=scores_by_key,
        )

        all_results[
            class_enrollment.student_id
        ] = result

    # ---------------------------------------------------------
    # 11. CALCULATE CLASS POSITIONS
    # ---------------------------------------------------------

    positions = calculate_class_positions(
        all_results
    )

    # ---------------------------------------------------------
    # 12. GET THIS STUDENT'S RESULT
    # ---------------------------------------------------------

    computed = all_results.get(student_id)

    if computed is None:
        raise HTTPException(
            status_code=404,
            detail="Student result could not be computed",
        )

    # ---------------------------------------------------------
    # 13. GET ATTENDANCE
    # ---------------------------------------------------------

    attendance_record = db.scalar(
        select(StudentAttendance).where(
            StudentAttendance.student_id == student_id,
            StudentAttendance.academic_session_id
            == academic_session_id,
            StudentAttendance.term_id == term_id,
        )
    )

    attendance_summary = None

    if attendance_record is not None:
        attendance_percentage = (
            attendance_record.days_present
            / attendance_record.school_days
            * 100
        )

        attendance_summary = ReportSheetAttendance(
            school_days=attendance_record.school_days,
            days_present=attendance_record.days_present,
            days_absent=attendance_record.days_absent,
            attendance_percentage=round(
                attendance_percentage,
                2,
            ),
        )

    # ---------------------------------------------------------
    # 14. GET TEACHER / PRINCIPAL COMMENTS
    # ---------------------------------------------------------

    comment_record = db.scalar(
        select(TermReportComment).where(
            TermReportComment.student_id == student_id,
            TermReportComment.academic_session_id
            == academic_session_id,
            TermReportComment.term_id == term_id,
        )
    )

    comment_summary = None

    if comment_record is not None:
        comment_summary = ReportSheetComments(
            teacher_comment=(
                comment_record.teacher_comment
            ),
            principal_comment=(
                comment_record.principal_comment
            ),
        )

    # ---------------------------------------------------------
    # 15. BUILD FINAL REPORT
    # ---------------------------------------------------------

    return StudentReportSheetResponse(
        school_info=ReportSheetSchool(
            school_id=school.id,
            school_name=school.name,
            email=school.email,
            phone=school.phone,
            address=school.address,
            motto=school.motto,
            logo_url=school.logo_url,
        ),
        student=ReportSheetStudent(
            student_id=student.id,
            admission_number=student.admission_number,
            full_name=(
                f"{student.first_name} "
                f"{student.last_name}"
            ),
            gender=student.gender,
            date_of_birth=student.date_of_birth,
        ),

        class_info=ReportSheetClass(
            class_id=class_record.id,
            class_name=class_record.name,
            class_size=len(class_enrollments),
        ),

        term_info=ReportSheetTerm(
            academic_session_id=academic_session.id,
            academic_session_name=academic_session.name,
            term_id=term.id,
            term_name=term.name,
            closing_date=term.closing_date,
            next_term_resumption_date=(
                term.next_term_resumption_date
            ),
        ),

        subjects=computed["subjects"],

        performance=ReportSheetPerformanceSummary(
            total_score=computed["total_score"],
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
            class_position=positions.get(
                student.id
            ),
            result_status=computed[
                "result_status"
            ],
            performance_remark=computed[
                "remark"
            ],
        ),

        attendance=attendance_summary,
        comments=comment_summary,
    )
