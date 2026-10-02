from app.core.security import hash_password
from app.models.academic_session import AcademicSession
from app.models.class_model import Class
from app.models.class_teacher_assignment import ClassTeacherAssignment
from app.models.teacher import Teacher
from app.models.user import User


PASSWORD = "TestPassword123!"


def _login(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create_second_session(db, school):
    session = AcademicSession(
        school_id=school.id,
        name="2027/2028",
        is_current=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _create_second_teacher(db, school):
    user = User(
        email="teacher.same.school@example.com",
        password_hash=hash_password(PASSWORD),
        role="teacher",
        school_id=school.id,
        is_active=True,
    )
    db.add(user)
    db.flush()

    teacher = Teacher(
        user_id=user.id,
        school_id=school.id,
        employee_number="T002",
        first_name="Teacher",
        last_name="SameSchool",
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


def test_school_admin_can_create_class_teacher_assignment(
    client,
    school_admin,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = client.post(
        "/api/class-teacher-assignments",
        headers=_auth(token),
        json={
            "teacher_id": school_one_teacher.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["teacher_id"] == school_one_teacher.id
    assert data["class_id"] == school_one_class.id
    assert data["academic_session_id"] == academic_session_one.id
    assert data["id"] > 0


def test_class_can_have_only_one_class_teacher_per_session(
    client,
    db,
    school_one,
    school_admin,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    second_teacher = _create_second_teacher(db, school_one)
    token = _login(client, school_admin.email)

    first_response = client.post(
        "/api/class-teacher-assignments",
        headers=_auth(token),
        json={
            "teacher_id": school_one_teacher.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert first_response.status_code == 201, first_response.text

    second_response = client.post(
        "/api/class-teacher-assignments",
        headers=_auth(token),
        json={
            "teacher_id": second_teacher.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == (
            "This class already has a class teacher "
            "for the selected academic session"
        )
    )


def test_same_class_can_have_different_class_teacher_in_another_session(
    client,
    db,
    school_one,
    school_admin,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    second_teacher = _create_second_teacher(db, school_one)
    second_session = _create_second_session(db, school_one)
    token = _login(client, school_admin.email)

    first_response = client.post(
        "/api/class-teacher-assignments",
        headers=_auth(token),
        json={
            "teacher_id": school_one_teacher.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    second_response = client.post(
        "/api/class-teacher-assignments",
        headers=_auth(token),
        json={
            "teacher_id": second_teacher.id,
            "class_id": school_one_class.id,
            "academic_session_id": second_session.id,
        },
    )

    assert first_response.status_code == 201, first_response.text
    assert second_response.status_code == 201, second_response.text


def test_admin_cannot_assign_teacher_from_another_school(
    client,
    school_admin,
    school_two_teacher,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = client.post(
        "/api/class-teacher-assignments",
        headers=_auth(token),
        json={
            "teacher_id": school_two_teacher.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Teacher not found"


def test_admin_cannot_assign_class_from_another_school(
    client,
    school_admin,
    school_one_teacher,
    school_two_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = client.post(
        "/api/class-teacher-assignments",
        headers=_auth(token),
        json={
            "teacher_id": school_one_teacher.id,
            "class_id": school_two_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found"


def test_admin_can_list_and_get_own_school_assignment(
    client,
    db,
    school_admin,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    assignment = ClassTeacherAssignment(
        teacher_id=school_one_teacher.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    token = _login(client, school_admin.email)

    list_response = client.get(
        "/api/class-teacher-assignments",
        headers=_auth(token),
    )

    assert list_response.status_code == 200, list_response.text
    assert assignment.id in {
        item["id"] for item in list_response.json()
    }

    get_response = client.get(
        f"/api/class-teacher-assignments/{assignment.id}",
        headers=_auth(token),
    )

    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["id"] == assignment.id


def test_other_school_admin_cannot_view_assignment(
    client,
    db,
    other_school_admin,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    assignment = ClassTeacherAssignment(
        teacher_id=school_one_teacher.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    token = _login(client, other_school_admin.email)

    list_response = client.get(
        "/api/class-teacher-assignments",
        headers=_auth(token),
    )

    assert list_response.status_code == 200
    assert assignment.id not in {
        item["id"] for item in list_response.json()
    }

    get_response = client.get(
        f"/api/class-teacher-assignments/{assignment.id}",
        headers=_auth(token),
    )

    assert get_response.status_code == 404


def test_teacher_sees_own_class_teacher_assignment(
    client,
    db,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    assignment = ClassTeacherAssignment(
        teacher_id=school_one_teacher.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    token = _login(client, "teacher.one@example.com")

    response = client.get(
        "/api/class-teacher-assignments/me",
        headers=_auth(token),
    )

    assert response.status_code == 200, response.text

    assignment_ids = {item["id"] for item in response.json()}
    assert assignment.id in assignment_ids


def test_teacher_does_not_see_another_teachers_class_assignment(
    client,
    db,
    school_one,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    second_class = Class(
        school_id=school_one.id,
        name="Junior Secondary Two",
        code="JSS2-CTA",
        description="Second class for class teacher tests",
    )
    db.add(second_class)
    db.flush()

    second_teacher = _create_second_teacher(db, school_one)

    own_assignment = ClassTeacherAssignment(
        teacher_id=school_one_teacher.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    other_assignment = ClassTeacherAssignment(
        teacher_id=second_teacher.id,
        class_id=second_class.id,
        academic_session_id=academic_session_one.id,
    )

    db.add_all([own_assignment, other_assignment])
    db.commit()
    db.refresh(own_assignment)
    db.refresh(other_assignment)

    token = _login(client, "teacher.one@example.com")

    response = client.get(
        "/api/class-teacher-assignments/me",
        headers=_auth(token),
    )

    assert response.status_code == 200, response.text

    assignment_ids = {item["id"] for item in response.json()}

    assert own_assignment.id in assignment_ids
    assert other_assignment.id not in assignment_ids


def test_school_admin_cannot_use_class_teacher_me_endpoint(
    client,
    school_admin,
):
    token = _login(client, school_admin.email)

    response = client.get(
        "/api/class-teacher-assignments/me",
        headers=_auth(token),
    )

    assert response.status_code == 403


def test_teacher_cannot_create_class_teacher_assignment(
    client,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    token = _login(client, "teacher.one@example.com")

    response = client.post(
        "/api/class-teacher-assignments",
        headers=_auth(token),
        json={
            "teacher_id": school_one_teacher.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 403


def test_school_admin_can_delete_class_teacher_assignment(
    client,
    db,
    school_admin,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    assignment = ClassTeacherAssignment(
        teacher_id=school_one_teacher.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    assignment_id = assignment.id

    token = _login(client, school_admin.email)

    response = client.delete(
        f"/api/class-teacher-assignments/{assignment_id}",
        headers=_auth(token),
    )

    assert response.status_code == 204

    db.expire_all()


    assert db.get(ClassTeacherAssignment, assignment_id) is None


def test_other_school_admin_cannot_delete_assignment(
    client,
    db,
    other_school_admin,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    assignment = ClassTeacherAssignment(
        teacher_id=school_one_teacher.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    assignment_id = assignment.id

    token = _login(client, other_school_admin.email)

    response = client.delete(
        f"/api/class-teacher-assignments/{assignment_id}",
        headers=_auth(token),
    )

    assert response.status_code == 404
    assert db.get(ClassTeacherAssignment, assignment_id) is not None


def test_unauthenticated_user_cannot_view_my_class_teacher_assignments(
    client,
):
    response = client.get(
        "/api/class-teacher-assignments/me",
    )

    assert response.status_code == 401