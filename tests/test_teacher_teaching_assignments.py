from app.core.security import hash_password
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.teaching_assignment import TeachingAssignment
from app.models.user import User


def _login(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_teacher_sees_own_teaching_assignments(
    client,
    db,
    school_one_teacher,
    school_one_class,
    school_one_subject,
    academic_session_one,
):
    assignment = TeachingAssignment(
        teacher_id=school_one_teacher.id,
        subject_id=school_one_subject.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    token = _login(client, "teacher.one@example.com")

    response = client.get(
        "/api/teaching-assignments/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    assignment_ids = {item["id"] for item in response.json()}
    assert assignment.id in assignment_ids


def test_teacher_does_not_see_another_teachers_assignment(
    client,
    db,
    school_one,
    school_one_teacher,
    school_one_class,
    school_one_subject,
    academic_session_one,
):
    own_assignment = TeachingAssignment(
        teacher_id=school_one_teacher.id,
        subject_id=school_one_subject.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )
    db.add(own_assignment)

    second_user = User(
        email="teacher.same.school@example.com",
        password_hash=hash_password("TestPassword123!"),
        role="teacher",
        school_id=school_one.id,
        is_active=True,
    )
    db.add(second_user)
    db.flush()

    second_teacher = Teacher(
        user_id=second_user.id,
        school_id=school_one.id,
        employee_number="T002",
        first_name="Teacher",
        last_name="SameSchool",
    )
    db.add(second_teacher)
    db.flush()

    other_subject = Subject(
        school_id=school_one.id,
        name="Chemistry",
        code="CHEM-TA",
        description="Teacher assignment isolation subject",
    )
    db.add(other_subject)
    db.flush()

    other_assignment = TeachingAssignment(
        teacher_id=second_teacher.id,
        subject_id=other_subject.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )
    db.add(other_assignment)

    db.commit()
    db.refresh(own_assignment)
    db.refresh(other_assignment)

    token = _login(client, "teacher.one@example.com")

    response = client.get(
        "/api/teaching-assignments/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    assignment_ids = {item["id"] for item in response.json()}

    assert own_assignment.id in assignment_ids
    assert other_assignment.id not in assignment_ids


def test_school_admin_cannot_use_teacher_me_endpoint(
    client,
    school_admin,
):
    token = _login(client, school_admin.email)

    response = client.get(
        "/api/teaching-assignments/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_my_teaching_assignments(
    client,
):
    response = client.get("/api/teaching-assignments/me")

    assert response.status_code == 401
