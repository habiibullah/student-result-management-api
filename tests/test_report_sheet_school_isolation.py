def test_school_admin_cannot_read_other_school_student_report(
    client,
    other_school_admin,
    academic_session_one,
    first_term,
    school_one_student,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": other_school_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        f"/api/report-sheets/student/{school_one_student.id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        params={
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
        },
    )

    assert response.status_code == 404

from app.models.enrollment import Enrollment


def test_school_admin_can_read_own_school_student_report(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    enrollment = Enrollment(
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    db.add(enrollment)
    db.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": school_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        f"/api/report-sheets/student/{school_one_student.id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        params={
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
        },
    )

    assert response.status_code == 200, response.text

    report = response.json()

    assert report["student"]["student_id"] == (
        school_one_student.id
    )