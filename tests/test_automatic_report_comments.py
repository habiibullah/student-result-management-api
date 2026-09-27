from app.models.assessment import Assessment
from app.models.enrollment import Enrollment
from app.models.performance_comment_band import (
    PerformanceCommentBand,
)
from app.models.student_score import StudentScore
from app.models.term_report_comment import TermReportComment
from app.services.report_sheet_service import (
    build_student_report_sheet,
)


def prepare_result(
    db,
    student,
    class_record,
    subject,
    academic_session,
    term,
    ca1_score=15,
    ca2_score=15,
    exam_score=50,
):
    enrollment = Enrollment(
        student_id=student.id,
        class_id=class_record.id,
        academic_session_id=academic_session.id,
    )

    db.add(enrollment)
    db.flush()

    ca1 = Assessment(
        class_id=class_record.id,
        subject_id=subject.id,
        academic_session_id=academic_session.id,
        term_id=term.id,
        assessment_type="CA",
        sequence=1,
        name="CA 1",
        max_score=20,
    )

    ca2 = Assessment(
        class_id=class_record.id,
        subject_id=subject.id,
        academic_session_id=academic_session.id,
        term_id=term.id,
        assessment_type="CA",
        sequence=2,
        name="CA 2",
        max_score=20,
    )

    exam = Assessment(
        class_id=class_record.id,
        subject_id=subject.id,
        academic_session_id=academic_session.id,
        term_id=term.id,
        assessment_type="EXAM",
        sequence=1,
        name="Examination",
        max_score=60,
    )

    db.add_all([ca1, ca2, exam])
    db.flush()

    db.add_all(
        [
            StudentScore(
                student_id=student.id,
                assessment_id=ca1.id,
                score=ca1_score,
            ),
            StudentScore(
                student_id=student.id,
                assessment_id=ca2.id,
                score=ca2_score,
            ),
            StudentScore(
                student_id=student.id,
                assessment_id=exam.id,
                score=exam_score,
            ),
        ]
    )

    db.commit()

    return ca1, ca2, exam


def add_band(
    db,
    school_id,
    minimum_average=80,
    maximum_average=100,
    teacher_comment="Excellent performance. Keep it up.",
    principal_comment="Excellent",
):
    band = PerformanceCommentBand(
        school_id=school_id,
        minimum_average=minimum_average,
        maximum_average=maximum_average,
        teacher_comment=teacher_comment,
        principal_comment=principal_comment,
    )

    db.add(band)
    db.commit()

    return band


def test_complete_result_uses_automatic_performance_comments(
    db,
    school_one,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
):
    prepare_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        subject=school_one_subject,
        academic_session=academic_session_one,
        term=first_term,
    )

    add_band(
        db=db,
        school_id=school_one.id,
        minimum_average=80,
        maximum_average=100,
    )

    report = build_student_report_sheet(
        db=db,
        school_id=school_one.id,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert report.performance.result_status == "COMPLETE"
    assert report.performance.average == 80
    assert report.comments is not None
    assert report.comments.teacher_comment == (
        "Excellent performance. Keep it up."
    )
    assert report.comments.principal_comment == "Excellent"


def test_manual_comments_override_automatic_comments(
    db,
    school_one,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
):
    prepare_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        subject=school_one_subject,
        academic_session=academic_session_one,
        term=first_term,
    )

    add_band(
        db=db,
        school_id=school_one.id,
    )

    db.add(
        TermReportComment(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
            teacher_comment="Manual teacher comment.",
            principal_comment="Manual principal comment.",
        )
    )
    db.commit()

    report = build_student_report_sheet(
        db=db,
        school_id=school_one.id,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert report.comments is not None
    assert report.comments.teacher_comment == (
        "Manual teacher comment."
    )
    assert report.comments.principal_comment == (
        "Manual principal comment."
    )


def test_manual_teacher_comment_and_automatic_principal_comment(
    db,
    school_one,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
):
    prepare_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        subject=school_one_subject,
        academic_session=academic_session_one,
        term=first_term,
    )

    add_band(
        db=db,
        school_id=school_one.id,
    )

    db.add(
        TermReportComment(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
            teacher_comment="Manual teacher comment.",
            principal_comment=None,
        )
    )
    db.commit()

    report = build_student_report_sheet(
        db=db,
        school_id=school_one.id,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert report.comments is not None
    assert report.comments.teacher_comment == (
        "Manual teacher comment."
    )
    assert report.comments.principal_comment == "Excellent"


def test_manual_principal_comment_and_automatic_teacher_comment(
    db,
    school_one,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
):
    prepare_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        subject=school_one_subject,
        academic_session=academic_session_one,
        term=first_term,
    )

    add_band(
        db=db,
        school_id=school_one.id,
    )

    db.add(
        TermReportComment(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
            teacher_comment=None,
            principal_comment="Manual principal comment.",
        )
    )
    db.commit()

    report = build_student_report_sheet(
        db=db,
        school_id=school_one.id,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert report.comments is not None
    assert report.comments.teacher_comment == (
        "Excellent performance. Keep it up."
    )
    assert report.comments.principal_comment == (
        "Manual principal comment."
    )


def test_whitespace_manual_comment_falls_back_to_automatic_comment(
    db,
    school_one,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
):
    prepare_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        subject=school_one_subject,
        academic_session=academic_session_one,
        term=first_term,
    )

    add_band(
        db=db,
        school_id=school_one.id,
    )

    db.add(
        TermReportComment(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
            teacher_comment="   ",
            principal_comment="   ",
        )
    )
    db.commit()

    report = build_student_report_sheet(
        db=db,
        school_id=school_one.id,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert report.comments is not None
    assert report.comments.teacher_comment == (
        "Excellent performance. Keep it up."
    )
    assert report.comments.principal_comment == "Excellent"


def test_school_uses_only_its_own_performance_comment_band(
    db,
    school_one,
    school_two,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
):
    prepare_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        subject=school_one_subject,
        academic_session=academic_session_one,
        term=first_term,
    )

    add_band(
        db=db,
        school_id=school_two.id,
        teacher_comment="Wrong school comment.",
        principal_comment="Wrong school principal comment.",
    )

    add_band(
        db=db,
        school_id=school_one.id,
        teacher_comment="Correct school comment.",
        principal_comment="Correct principal comment.",
    )

    report = build_student_report_sheet(
        db=db,
        school_id=school_one.id,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert report.comments is not None
    assert report.comments.teacher_comment == (
        "Correct school comment."
    )
    assert report.comments.principal_comment == (
        "Correct principal comment."
    )

def test_incomplete_result_does_not_use_automatic_comments(
    db,
    school_one,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
):
    enrollment = Enrollment(
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    db.add(enrollment)
    db.flush()

    ca1 = Assessment(
        class_id=school_one_class.id,
        subject_id=school_one_subject.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        assessment_type="CA",
        sequence=1,
        name="CA 1",
        max_score=20,
    )

    db.add(ca1)
    db.flush()

    db.add(
        StudentScore(
            student_id=school_one_student.id,
            assessment_id=ca1.id,
            score=18,
        )
    )

    db.commit()

    add_band(
        db=db,
        school_id=school_one.id,
        minimum_average=0,
        maximum_average=100,
        teacher_comment="This must not appear.",
        principal_comment="This must not appear.",
    )

    report = build_student_report_sheet(
        db=db,
        school_id=school_one.id,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert report.performance.result_status == "INCOMPLETE"
    assert report.comments is None