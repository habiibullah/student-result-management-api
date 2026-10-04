from app.models import ClassTeacherAssignment, Enrollment


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


def _assign_class_teacher(
    db,
    teacher,
    class_,
    academic_session,
):
    assignment = ClassTeacherAssignment(
        teacher_id=teacher.id,
        class_id=class_.id,
        academic_session_id=academic_session.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def _enroll_student(
    db,
    student,
    class_,
    academic_session,
):
    enrollment = Enrollment(
        student_id=student.id,
        class_id=class_.id,
        academic_session_id=academic_session.id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return enrollment


def test_class_teacher_can_list_assigned_class_enrollments(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    enrollment = _enroll_student(
        db,
        school_one_student,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.get(
        "/api/enrollments/class-teacher",
        headers=_auth(token),
        params={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == enrollment.id
    assert data[0]["student_id"] == school_one_student.id
    assert data[0]["class_id"] == school_one_class.id
    assert (
        data[0]["academic_session_id"]
        == academic_session_one.id
    )


def test_class_teacher_can_list_students_in_assigned_class(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    _enroll_student(
        db,
        school_one_student,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.get(
        "/api/students/class-teacher",
        headers=_auth(token),
        params={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == school_one_student.id
    assert (
        data[0]["admission_number"]
        == school_one_student.admission_number
    )


def test_unassigned_teacher_cannot_list_class_enrollments(
    client,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_one_teacher.user.email)

    response = client.get(
        "/api/enrollments/class-teacher",
        headers=_auth(token),
        params={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Class teacher access required"
    )


def test_unassigned_teacher_cannot_list_class_students(
    client,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_one_teacher.user.email)

    response = client.get(
        "/api/students/class-teacher",
        headers=_auth(token),
        params={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Class teacher access required"
    )


def test_class_teacher_cannot_access_different_class(
    client,
    db,
    school_one_teacher,
    school_one_class,
    school_two_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    enrollment_response = client.get(
        "/api/enrollments/class-teacher",
        headers=_auth(token),
        params={
            "class_id": school_two_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    student_response = client.get(
        "/api/students/class-teacher",
        headers=_auth(token),
        params={
            "class_id": school_two_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert enrollment_response.status_code == 403
    assert student_response.status_code == 403