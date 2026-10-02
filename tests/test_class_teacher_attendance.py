from app.core.security import hash_password
from app.models.class_model import Class
from app.models.class_teacher_assignment import ClassTeacherAssignment
from app.models.enrollment import Enrollment
from app.models.student_attendance import StudentAttendance
from app.models.teacher import Teacher
from app.models.user import User


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


def create_class_teacher_assignment(
    db,
    teacher_id,
    class_id,
    academic_session_id,
):
    assignment = ClassTeacherAssignment(
        teacher_id=teacher_id,
        class_id=class_id,
        academic_session_id=academic_session_id,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def create_teacher(
    db,
    school,
    email,
    employee_number,
):
    user = User(
        email=email,
        password_hash=hash_password("TestPassword123!"),
        role="teacher",
        school_id=school.id,
        is_active=True,
    )

    db.add(user)
    db.flush()

    teacher = Teacher(
        user_id=user.id,
        school_id=school.id,
        employee_number=employee_number,
        first_name="Attendance",
        last_name="Teacher",
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


def create_second_class(db, school):
    class_ = Class(
        school_id=school.id,
        name="Attendance Test Class",
        code="ATT-CLASS-2",
        description="Second class for attendance authorization tests",
    )

    db.add(class_)
    db.commit()
    db.refresh(class_)

    return class_


def create_attendance(
    db,
    student_id,
    academic_session_id,
    term_id,
    school_days=60,
    days_present=55,
):
    attendance = StudentAttendance(
        student_id=student_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        school_days=school_days,
        days_present=days_present,
        days_absent=school_days - days_present,
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return attendance


def prepare_class_teacher(
    db,
    school,
    student,
    class_,
    academic_session,
):
    teacher = create_teacher(
        db=db,
        school=school,
        email="attendance.teacher@example.com",
        employee_number="ATT-T001",
    )

    create_enrollment(
        db=db,
        student_id=student.id,
        class_id=class_.id,
        academic_session_id=academic_session.id,
    )

    create_class_teacher_assignment(
        db=db,
        teacher_id=teacher.id,
        class_id=class_.id,
        academic_session_id=academic_session.id,
    )

    return teacher


def configure_school_days(db, term, school_days=60):
    term.school_days = school_days
    db.commit()
    db.refresh(term)


# ============================================================
# DERIVED ATTENDANCE
# ============================================================


def test_class_teacher_attendance_derives_school_days_and_absence(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )
    configure_school_days(db, first_term, 60)

    token = login(client, teacher.user.email)

    response = client.post(
        "/api/student-attendance/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "days_present": 55,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["school_days"] == 60
    assert data["days_present"] == 55
    assert data["days_absent"] == 5


def test_class_teacher_attendance_requires_configured_school_days(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )

    first_term.school_days = None
    db.commit()

    token = login(client, teacher.user.email)

    response = client.post(
        "/api/student-attendance/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "days_present": 55,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "School days must be configured for "
        "this term before attendance can be entered"
    )


def test_class_teacher_attendance_rejects_excessive_days_present(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )
    configure_school_days(db, first_term, 60)

    token = login(client, teacher.user.email)

    response = client.post(
        "/api/student-attendance/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "days_present": 61,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Days present cannot exceed school days"
    )


def test_class_teacher_cannot_supply_school_days(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )
    configure_school_days(db, first_term, 60)

    token = login(client, teacher.user.email)

    response = client.post(
        "/api/student-attendance/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "days_present": 55,
            "school_days": 100,
        },
    )

    assert response.status_code == 422


def test_class_teacher_cannot_supply_days_absent(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )
    configure_school_days(db, first_term, 60)

    token = login(client, teacher.user.email)

    response = client.post(
        "/api/student-attendance/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "days_present": 55,
            "days_absent": 5,
        },
    )

    assert response.status_code == 422


# ============================================================
# AUTHORIZATION
# ============================================================


def test_unassigned_teacher_cannot_create_attendance(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    teacher = create_teacher(
        db,
        school_one,
        "attendance.unassigned@example.com",
        "ATT-T002",
    )

    configure_school_days(db, first_term, 60)

    token = login(client, teacher.user.email)

    response = client.post(
        "/api/student-attendance/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "days_present": 55,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Class teacher access required"
    )


def test_class_teacher_cannot_create_attendance_for_another_class(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = create_teacher(
        db,
        school_one,
        "attendance.otherclass@example.com",
        "ATT-T003",
    )

    second_class = create_second_class(db, school_one)

    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    create_class_teacher_assignment(
        db,
        teacher.id,
        second_class.id,
        academic_session_one.id,
    )

    configure_school_days(db, first_term, 60)

    token = login(client, teacher.user.email)

    response = client.post(
        "/api/student-attendance/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "days_present": 55,
        },
    )

    assert response.status_code == 403


# ============================================================
# READ + UPDATE
# ============================================================


def test_assigned_class_teacher_can_read_attendance(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )

    attendance = create_attendance(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, teacher.user.email)

    response = client.get(
        f"/api/student-attendance/class-teacher/{attendance.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == attendance.id


def test_class_teacher_list_contains_only_assigned_attendance(
    client,
    db,
    school_one,
    school_one_student,
    school_two_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )

    own_attendance = create_attendance(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, teacher.user.email)

    response = client.get(
        "/api/student-attendance/class-teacher",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        record["id"]
        for record in response.json()
    }

    assert own_attendance.id in returned_ids


def test_class_teacher_update_recalculates_attendance(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )

    configure_school_days(db, first_term, 60)

    attendance = create_attendance(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
        school_days=60,
        days_present=50,
    )

    token = login(client, teacher.user.email)

    response = client.patch(
        f"/api/student-attendance/class-teacher/{attendance.id}",
        headers=auth_headers(token),
        json={
            "days_present": 56,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["school_days"] == 60
    assert data["days_present"] == 56
    assert data["days_absent"] == 4


def test_class_teacher_update_uses_current_term_school_days(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )

    attendance = create_attendance(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
        school_days=60,
        days_present=55,
    )

    configure_school_days(db, first_term, 62)

    token = login(client, teacher.user.email)

    response = client.patch(
        f"/api/student-attendance/class-teacher/{attendance.id}",
        headers=auth_headers(token),
        json={
            "days_present": 57,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["school_days"] == 62
    assert data["days_present"] == 57
    assert data["days_absent"] == 5


# ============================================================
# HISTORICAL READ
# ============================================================


def test_class_teacher_historical_attendance_remains_readable(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )

    attendance = create_attendance(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    active_subscription.status = "expired"
    db.commit()

    token = login(client, teacher.user.email)

    response = client.get(
        f"/api/student-attendance/class-teacher/{attendance.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200


# ============================================================
# SUBSCRIPTION
# ============================================================


def test_inactive_subscription_blocks_class_teacher_update(
    client,
    db,
    school_one,
    school_one_student,
    school_one_class,
    academic_session_one,
    second_term,
    pending_subscription,
):
    teacher = prepare_class_teacher(
        db,
        school_one,
        school_one_student,
        school_one_class,
        academic_session_one,
    )

    configure_school_days(db, second_term, 60)

    attendance = create_attendance(
        db,
        school_one_student.id,
        academic_session_one.id,
        second_term.id,
    )

    token = login(client, teacher.user.email)

    response = client.patch(
        f"/api/student-attendance/class-teacher/{attendance.id}",
        headers=auth_headers(token),
        json={
            "days_present": 56,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "An active subscription is required "
        "for this academic term"
    )


# ============================================================
# ADMIN OVERSIGHT
# ============================================================


def test_admin_can_use_class_teacher_attendance_route(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    configure_school_days(db, first_term, 60)

    token = login(client, school_admin.email)

    response = client.post(
        "/api/student-attendance/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "days_present": 58,
        },
    )

    assert response.status_code == 201
    assert response.json()["days_absent"] == 2
