from app.models.student import Student

from tests.test_class_report_summary import (
    auth_headers,
    create_enrollment,
    login,
    prepare_complete_result,
)


def get_class_analytics(
    client,
    token,
    class_id,
    academic_session_id,
    term_id,
):
    return client.get(
        f"/api/analytics/classes/{class_id}",
        headers=auth_headers(token),
        params={
            "academic_session_id": academic_session_id,
            "term_id": term_id,
        },
    )


def test_class_analytics_returns_statistics(
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

    response = get_class_analytics(
        client=client,
        token=token,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["class_id"] == school_one_class.id
    assert data["class_name"] == school_one_class.name
    assert data["academic_session_id"] == academic_session_one.id
    assert data["term_id"] == first_term.id

    assert data["enrolled_students"] == 1
    assert data["complete_results"] == 1
    assert data["incomplete_results"] == 0

    assert data["highest_average"] == 90
    assert data["lowest_average"] == 90
    assert data["class_average"] == 90

    assert len(data["subjects"]) == 1

    subject = data["subjects"][0]

    assert subject["subject_id"] == (
        active_term_assessment.subject_id
    )
    assert subject["class_average"] == 90
    assert subject["completed_students"] == 1


def test_class_analytics_rejects_other_school_class(
    client,
    school_admin,
    school_two_class,
    academic_session_one,
    first_term,
):
    token = login(client, school_admin.email)

    response = get_class_analytics(
        client=client,
        token=token,
        class_id=school_two_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found"


def test_class_analytics_rejects_term_from_another_session(
    client,
    school_admin,
    school_one_class,
    academic_session_one,
    school_two_term,
):
    token = login(client, school_admin.email)

    response = get_class_analytics(
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

def test_class_analytics_handles_complete_and_incomplete_results(
    client,
    db,
    school_admin,
    school_one,
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

    incomplete_student = Student(
        user_id=None,
        school_id=school_one.id,
        admission_number="SCH1/002",
        first_name="Mariam",
        last_name="Ali",
        date_of_birth=None,
        gender=None,
    )

    db.add(incomplete_student)
    db.commit()
    db.refresh(incomplete_student)

    create_enrollment(
        db=db,
        student_id=incomplete_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    token = login(client, school_admin.email)

    response = get_class_analytics(
        client=client,
        token=token,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["enrolled_students"] == 2
    assert data["complete_results"] == 1
    assert data["incomplete_results"] == 1

    assert data["highest_average"] == 90
    assert data["lowest_average"] == 90
    assert data["class_average"] == 90

    assert len(data["subjects"]) == 1

    subject = data["subjects"][0]

    assert subject["class_average"] == 90
    assert subject["completed_students"] == 1

def test_class_analytics_handles_no_assessments(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    token = login(client, school_admin.email)

    response = get_class_analytics(
        client=client,
        token=token,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["enrolled_students"] == 1
    assert data["complete_results"] == 0
    assert data["incomplete_results"] == 1

    assert data["highest_average"] is None
    assert data["lowest_average"] is None
    assert data["class_average"] is None

    assert data["subjects"] == []