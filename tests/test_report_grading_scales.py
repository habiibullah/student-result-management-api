from app.models.grading_scale import GradingScale
from app.services.report_sheet_service import build_student_report_sheet
from app.models.enrollment import Enrollment

def build_report(
    db,
    school,
    student,
    class_record,
    academic_session,
    term,
):
    enrollment = Enrollment(
        student_id=student.id,
        class_id=class_record.id,
        academic_session_id=academic_session.id,
    )

    db.add(enrollment)
    db.commit()

    return build_student_report_sheet(
        db=db,
        school_id=school.id,
        student_id=student.id,
        academic_session_id=academic_session.id,
        term_id=term.id,
    )

def test_report_includes_configured_grading_scales(
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    scales = [
        GradingScale(
            school_id=school_one.id,
            grade="A",
            minimum_score=70,
            maximum_score=100,
            remark="Excellent",
        ),
        GradingScale(
            school_id=school_one.id,
            grade="B",
            minimum_score=60,
            maximum_score=69.99,
            remark="Very Good",
        ),
        GradingScale(
            school_id=school_one.id,
            grade="C",
            minimum_score=50,
            maximum_score=59.99,
            remark="Good",
        ),
        GradingScale(
            school_id=school_one.id,
            grade="D",
            minimum_score=45,
            maximum_score=49.99,
            remark="Fair",
        ),
        GradingScale(
            school_id=school_one.id,
            grade="E",
            minimum_score=40,
            maximum_score=44.99,
            remark="Pass",
        ),
        GradingScale(
            school_id=school_one.id,
            grade="F",
            minimum_score=0,
            maximum_score=39.99,
            remark="Fail",
        ),
    ]

    db.add_all(scales)
    db.commit()

    report = build_report(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
        first_term,
    )

    assert len(report.grading_scales) == 6

    assert [
        scale.grade for scale in report.grading_scales
    ] == ["A", "B", "C", "D", "E", "F"]

    assert report.grading_scales[0].minimum_score == 70
    assert report.grading_scales[0].maximum_score == 100
    assert report.grading_scales[0].remark == "Excellent"

    assert report.grading_scales[-1].minimum_score == 0
    assert report.grading_scales[-1].maximum_score == 39.99
    assert report.grading_scales[-1].remark == "Fail"


def test_report_grading_scales_are_ordered_by_minimum_score_descending(
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    db.add_all(
        [
            GradingScale(
                school_id=school_one.id,
                grade="F",
                minimum_score=0,
                maximum_score=39.99,
                remark="Fail",
            ),
            GradingScale(
                school_id=school_one.id,
                grade="A",
                minimum_score=70,
                maximum_score=100,
                remark="Excellent",
            ),
            GradingScale(
                school_id=school_one.id,
                grade="C",
                minimum_score=50,
                maximum_score=59.99,
                remark="Good",
            ),
        ]
    )
    db.commit()

    report = build_report(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
        first_term,
    )

    assert [
        scale.minimum_score
        for scale in report.grading_scales
    ] == [70, 50, 0]

    assert [
        scale.grade for scale in report.grading_scales
    ] == ["A", "C", "F"]


def test_report_grading_scales_are_school_scoped(
    db,
    school_one,
    school_two,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    db.add_all(
        [
            GradingScale(
                school_id=school_one.id,
                grade="A",
                minimum_score=70,
                maximum_score=100,
                remark="School One Excellent",
            ),
            GradingScale(
                school_id=school_two.id,
                grade="X",
                minimum_score=80,
                maximum_score=100,
                remark="School Two Scale",
            ),
        ]
    )
    db.commit()

    report = build_report(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
        first_term,
    )

    assert len(report.grading_scales) == 1
    assert report.grading_scales[0].grade == "A"
    assert (
        report.grading_scales[0].remark
        == "School One Excellent"
    )


def test_report_returns_empty_grading_scales_when_none_configured(
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    report = build_report(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
        first_term,
    )

    assert report.grading_scales == []
