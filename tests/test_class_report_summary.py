from app.models.assessment import Assessment
from app.models.class_model import Class
from app.models.enrollment import Enrollment
from app.models.student_score import StudentScore


def login(
    client,
    email,
    password="TestPassword123!",
):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_enrollment(
    db,
    student_id,
    class_id,
    academic_session_id,
):
    enrollment = Enrollment(
        student_id=student_id,
        class_id=class_id,
        academic_session_id=academic_session_id,
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return enrollment


def create_score(
    db,
    student_id,
    assessment_id,
    score,
):
    student_score = StudentScore(
        student_id=student_id,
        assessment_id=assessment_id,
        score=score,
    )

    db.add(student_score)
    db.commit()
    db.refresh(student_score)

    return student_score


def prepare_complete_result(
    db,
    student,
    class_record,
    academic_session,
    assessment,
):
    create_enrollment(
        db=db,
        student_id=student.id,
        class_id=class_record.id,
        academic_session_id=academic_session.id,
    )

    ca2 = Assessment(
        class_id=class_record.id,
        subject_id=assessment.subject_id,
        academic_session_id=academic_session.id,
        term_id=assessment.term_id,
        assessment_type="CA",
        sequence=2,
        name="CA 2",
        max_score=20,
    )

    exam = Assessment(
        class_id=class_record.id,
        subject_id=assessment.subject_id,
        academic_session_id=academic_session.id,
        term_id=assessment.term_id,
        assessment_type="EXAM",
        sequence=1,
        name="Examination",
        max_score=60,
    )

    db.add_all([ca2, exam])
    db.commit()

    db.refresh(ca2)
    db.refresh(exam)

    create_score(
        db=db,
        student_id=student.id,
        assessment_id=assessment.id,
        score=18,
    )

    create_score(
        db=db,
        student_id=student.id,
        assessment_id=ca2.id,
        score=17,
    )

    create_score(
        db=db,
        student_id=student.id,
        assessment_id=exam.id,
        score=55,
    )


def get_class_report_summary(
    client,
    token,
    class_id,
    academic_session_id,
    term_id,
):
    return client.get(
        "/api/report-sheets/class-summary",
        headers=auth_headers(token),
        params={
            "class_id": class_id,
            "academic_session_id": academic_session_id,
            "term_id": term_id,
        },
    )


def test_class_report_summary_returns_complete_student(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_term_assessment,
):
    prepare_complete_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        academic_session=academic_session_one,
        assessment=active_term_assessment,
    )

    token = login(client, school_admin.email)

    response = get_class_report_summary(
        client=client,
        token=token,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    student = data[0]

    assert student["student_id"] == school_one_student.id
    assert student["admission_number"] == (
        school_one_student.admission_number
    )
    assert student["result_status"] == "COMPLETE"
    assert student["number_of_subjects"] == 1
    assert student["completed_subjects"] == 1
    assert student["average"] == 90
    assert student["overall_grade"] is not None


def test_class_report_summary_returns_incomplete_student(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_term_assessment,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    token = login(client, school_admin.email)

    response = get_class_report_summary(
        client=client,
        token=token,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    student = data[0]

    assert student["student_id"] == school_one_student.id
    assert student["result_status"] == "INCOMPLETE"
    assert student["number_of_subjects"] == 1
    assert student["completed_subjects"] == 0
    assert student["average"] is None
    assert student["overall_grade"] is None


def test_class_report_summary_returns_only_selected_class(
    client,
    db,
    school_admin,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    second_class = Class(
        school_id=school_one.id,
        name="Second Test Class",
        code="STC",
    )

    db.add(second_class)
    db.commit()
    db.refresh(second_class)

    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=second_class.id,
        academic_session_id=academic_session_one.id,
    )

    token = login(client, school_admin.email)

    response = get_class_report_summary(
        client=client,
        token=token,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert response.status_code == 200
    assert response.json() == []

def test_class_report_summary_rejects_other_school_class(
    client,
    school_admin,
    school_two_class,
    academic_session_one,
    first_term,
):
    token = login(client, school_admin.email)

    response = get_class_report_summary(
        client=client,
        token=token,
        class_id=school_two_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert response.status_code == 404


def test_class_report_summary_rejects_term_from_another_session(
    client,
    school_admin,
    school_one_class,
    academic_session_one,
    school_two_term,
):
    token = login(client, school_admin.email)

    response = get_class_report_summary(
        client=client,
        token=token,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=school_two_term.id,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
      "Term does not belong to the selected academic session"
    )