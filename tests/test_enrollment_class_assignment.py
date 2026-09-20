from app.models import Class
from app.models.academic_session import AcademicSession
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enrollment import Enrollment

def login(client, email, password="TestPassword123!"):
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


def test_school_admin_can_assign_student_to_class(
    client,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    token = login(client, school_admin.email)

    response = client.post(
        "/api/enrollments",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 201

    enrollment = response.json()

    assert enrollment["id"] > 0
    assert enrollment["student_id"] == school_one_student.id
    assert enrollment["class_id"] == school_one_class.id
    assert (
        enrollment["academic_session_id"]
        == academic_session_one.id
    )

def test_student_cannot_be_assigned_to_two_classes_in_same_session(
    client,
    db,
    school_admin,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    second_class = Class(
        school_id=school_one.id,
        name="Junior Secondary Two",
        code="JSS2",
        description="Second class for enrolment testing",
    )

    db.add(second_class)
    db.commit()
    db.refresh(second_class)

    token = login(client, school_admin.email)
    headers = auth_headers(token)

    first_response = client.post(
        "/api/enrollments",
        headers=headers,
        json={
            "student_id": school_one_student.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/enrollments",
        headers=headers,
        json={
            "student_id": school_one_student.id,
            "class_id": second_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Student is already assigned to a class "
        "for this academic session"
    )

def test_school_admin_can_change_students_class_assignment(
    client,
    db,
    school_admin,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    second_class = Class(
        school_id=school_one.id,
        name="Junior Secondary Two",
        code="JSS2",
        description="Second class for enrolment testing",
    )

    db.add(second_class)
    db.commit()
    db.refresh(second_class)

    token = login(client, school_admin.email)
    headers = auth_headers(token)

    create_response = client.post(
        "/api/enrollments",
        headers=headers,
        json={
            "student_id": school_one_student.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert create_response.status_code == 201
    enrollment_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/enrollments/{enrollment_id}",
        headers=headers,
        json={"class_id": second_class.id},
    )

    assert update_response.status_code == 200

    updated_enrollment = update_response.json()

    assert updated_enrollment["id"] == enrollment_id
    assert updated_enrollment["student_id"] == school_one_student.id
    assert updated_enrollment["class_id"] == second_class.id
    assert (
        updated_enrollment["academic_session_id"]
        == academic_session_one.id
        )

def test_student_can_have_class_assignments_in_different_sessions(
    client,
    db,
    school_admin,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    second_class = Class(
        school_id=school_one.id,
        name="Junior Secondary Two",
        code="JSS2",
        description="Second class for enrolment testing",
    )

    next_session = AcademicSession(
        school_id=school_one.id,
        name="2027/2028",
        is_current=False,
    )

    db.add_all([second_class, next_session])
    db.commit()
    db.refresh(second_class)
    db.refresh(next_session)

    token = login(client, school_admin.email)
    headers = auth_headers(token)

    first_response = client.post(
        "/api/enrollments",
        headers=headers,
        json={
            "student_id": school_one_student.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert first_response.status_code == 201
    first_enrollment = first_response.json()

    second_response = client.post(
        "/api/enrollments",
        headers=headers,
        json={
            "student_id": school_one_student.id,
            "class_id": second_class.id,
            "academic_session_id": next_session.id,
        },
    )

    assert second_response.status_code == 201
    second_enrollment = second_response.json()

    assert second_enrollment["id"] != first_enrollment["id"]
    assert second_enrollment["class_id"] == second_class.id
    assert second_enrollment["academic_session_id"] == next_session.id

    previous_response = client.get(
        f"/api/enrollments/{first_enrollment['id']}",
        headers=headers,
    )

    assert previous_response.status_code == 200
    assert previous_response.json()["class_id"] == school_one_class.id
    assert (
        previous_response.json()["academic_session_id"]
        == academic_session_one.id
    )

def test_updating_enrollment_cannot_duplicate_another_session_assignment(
    client,
    db,
    school_admin,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    second_class = Class(
        school_id=school_one.id,
        name="Junior Secondary Two",
        code="JSS2",
        description="Second class for enrolment testing",
    )

    next_session = AcademicSession(
        school_id=school_one.id,
        name="2027/2028",
        is_current=False,
    )

    db.add_all([second_class, next_session])
    db.commit()
    db.refresh(second_class)
    db.refresh(next_session)

    token = login(client, school_admin.email)
    headers = auth_headers(token)

    first_response = client.post(
        "/api/enrollments",
        headers=headers,
        json={
            "student_id": school_one_student.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert first_response.status_code == 201
    first_enrollment_id = first_response.json()["id"]

    second_response = client.post(
        "/api/enrollments",
        headers=headers,
        json={
            "student_id": school_one_student.id,
            "class_id": second_class.id,
            "academic_session_id": next_session.id,
        },
    )

    assert second_response.status_code == 201
    second_enrollment_id = second_response.json()["id"]

    update_response = client.patch(
        f"/api/enrollments/{first_enrollment_id}",
        headers=headers,
        json={
            "academic_session_id": next_session.id,
        },
    )

    assert update_response.status_code == 409
    assert update_response.json()["detail"] == (
        "Student is already assigned to a class "
        "for this academic session"
    )

    first_enrollment_response = client.get(
        f"/api/enrollments/{first_enrollment_id}",
        headers=headers,
    )

    assert first_enrollment_response.status_code == 200
    assert (
        first_enrollment_response.json()["academic_session_id"]
        == academic_session_one.id
    )

    second_enrollment_response = client.get(
        f"/api/enrollments/{second_enrollment_id}",
        headers=headers,
    )

    assert second_enrollment_response.status_code == 200
    assert (
        second_enrollment_response.json()["academic_session_id"]
        == next_session.id
    )


def test_database_rejects_two_classes_for_student_in_same_session(
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    second_class = Class(
        school_id=school_one.id,
        name="Junior Secondary Two",
        code="JSS2",
        description="Second class for enrolment testing",
    )

    db.add(second_class)
    db.commit()
    db.refresh(second_class)

    first_enrollment = Enrollment(
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    db.add(first_enrollment)
    db.commit()

    duplicate_enrollment = Enrollment(
        student_id=school_one_student.id,
        class_id=second_class.id,
        academic_session_id=academic_session_one.id,
    )

    db.add(duplicate_enrollment)

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()
