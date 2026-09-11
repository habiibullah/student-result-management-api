from app.models.enrollment import Enrollment
from app.models.student_attendance import StudentAttendance


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


def attendance_payload(
    student_id,
    academic_session_id,
    term_id,
    school_days=60,
    days_present=55,
    days_absent=5,
):
    return {
        "student_id": student_id,
        "academic_session_id": academic_session_id,
        "term_id": term_id,
        "school_days": school_days,
        "days_present": days_present,
        "days_absent": days_absent,
    }


def assert_subscription_required(response):
    assert response.status_code == 403

    assert response.json()["detail"] == (
        "An active subscription is required "
        "for this academic term"
    )


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


def create_attendance_record(
    db,
    student_id,
    academic_session_id,
    term_id,
    school_days=60,
    days_present=55,
    days_absent=5,
):
    attendance = StudentAttendance(
        student_id=student_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        school_days=school_days,
        days_present=days_present,
        days_absent=days_absent,
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return attendance


# ============================================================
# CREATE
# ============================================================


def test_active_subscription_allows_attendance_creation(
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
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-attendance",
        headers=auth_headers(token),
        json=attendance_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["student_id"] == school_one_student.id
    assert data["academic_session_id"] == (
        academic_session_one.id
    )
    assert data["term_id"] == first_term.id
    assert data["school_days"] == 60
    assert data["days_present"] == 55
    assert data["days_absent"] == 5


def test_pending_subscription_blocks_attendance_creation(
    client,
    school_admin,
    school_one_student,
    academic_session_one,
    second_term,
    pending_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-attendance",
        headers=auth_headers(token),
        json=attendance_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=second_term.id,
        ),
    )

    assert_subscription_required(response)


def test_cancelled_subscription_blocks_attendance_creation(
    client,
    school_admin,
    school_one_student,
    academic_session_one,
    third_term,
    cancelled_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-attendance",
        headers=auth_headers(token),
        json=attendance_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=third_term.id,
        ),
    )

    assert_subscription_required(response)


def test_expired_subscription_blocks_attendance_creation(
    client,
    school_admin,
    school_one_student,
    academic_session_one,
    test_extra_term,
    expired_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-attendance",
        headers=auth_headers(token),
        json=attendance_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=test_extra_term.id,
        ),
    )

    assert_subscription_required(response)


def test_missing_subscription_blocks_attendance_creation(
    client,
    school_admin,
    school_one_student,
    academic_session_one,
    unsubscribed_term,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-attendance",
        headers=auth_headers(token),
        json=attendance_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=unsubscribed_term.id,
        ),
    )

    assert_subscription_required(response)


# ============================================================
# UPDATE
# ============================================================


def test_active_subscription_allows_attendance_update(
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
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    attendance = create_attendance_record(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            "/api/student-attendance/"
            f"{attendance.id}"
        ),
        headers=auth_headers(token),
        json={
            "school_days": 60,
            "days_present": 56,
            "days_absent": 4,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["school_days"] == 60
    assert data["days_present"] == 56
    assert data["days_absent"] == 4


def test_inactive_subscription_blocks_attendance_update(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    second_term,
    pending_subscription,
):
    attendance = create_attendance_record(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            "/api/student-attendance/"
            f"{attendance.id}"
        ),
        headers=auth_headers(token),
        json={
            "school_days": 60,
            "days_present": 56,
            "days_absent": 4,
        },
    )

    assert_subscription_required(response)


# ============================================================
# DELETE
# ============================================================


def test_active_subscription_allows_attendance_delete(
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
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    attendance = create_attendance_record(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        (
            "/api/student-attendance/"
            f"{attendance.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 204


def test_inactive_subscription_blocks_attendance_delete(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    second_term,
    pending_subscription,
):
    attendance = create_attendance_record(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        (
            "/api/student-attendance/"
            f"{attendance.id}"
        ),
        headers=auth_headers(token),
    )

    assert_subscription_required(response)


# ============================================================
# HISTORICAL READ ACCESS
# ============================================================


def test_historical_attendance_remains_readable_after_subscription_expires(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
    active_subscription,
):
    attendance = create_attendance_record(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    active_subscription.status = "expired"

    db.commit()
    db.refresh(active_subscription)

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        (
            "/api/student-attendance/"
            f"{attendance.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == attendance.id
    assert data["student_id"] == school_one_student.id


def test_historical_attendance_list_remains_available_after_subscription_expires(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
    active_subscription,
):
    attendance = create_attendance_record(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    active_subscription.status = "expired"

    db.commit()
    db.refresh(active_subscription)

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/student-attendance",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        record["id"]
        for record in response.json()
    }

    assert attendance.id in returned_ids


# ============================================================
# TENANT ISOLATION
# ============================================================


def test_school_admin_cannot_read_other_school_attendance(
    client,
    db,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
    school_two_subscription,
):
    attendance = create_attendance_record(
        db=db,
        student_id=school_two_student.id,
        academic_session_id=academic_session_two.id,
        term_id=school_two_term.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        (
            "/api/student-attendance/"
            f"{attendance.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Attendance record not found"
    )


def test_school_admin_cannot_update_other_school_attendance(
    client,
    db,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
    school_two_subscription,
):
    attendance = create_attendance_record(
        db=db,
        student_id=school_two_student.id,
        academic_session_id=academic_session_two.id,
        term_id=school_two_term.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            "/api/student-attendance/"
            f"{attendance.id}"
        ),
        headers=auth_headers(token),
        json={
            "school_days": 60,
            "days_present": 56,
            "days_absent": 4,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Attendance record not found"
    )


def test_school_admin_cannot_delete_other_school_attendance(
    client,
    db,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
    school_two_subscription,
):
    attendance = create_attendance_record(
        db=db,
        student_id=school_two_student.id,
        academic_session_id=academic_session_two.id,
        term_id=school_two_term.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        (
            "/api/student-attendance/"
            f"{attendance.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Attendance record not found"
    )


def test_attendance_list_does_not_expose_other_school_records(
    client,
    db,
    school_admin,
    school_one_student,
    school_two_student,
    academic_session_one,
    academic_session_two,
    first_term,
    school_two_term,
    active_subscription,
    school_two_subscription,
):
    own_attendance = create_attendance_record(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    other_attendance = create_attendance_record(
        db=db,
        student_id=school_two_student.id,
        academic_session_id=academic_session_two.id,
        term_id=school_two_term.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/student-attendance",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        record["id"]
        for record in response.json()
    }

    assert own_attendance.id in returned_ids
    assert other_attendance.id not in returned_ids


# ============================================================
# ATTENDANCE VALUE VALIDATION
# ============================================================


def test_invalid_attendance_totals_are_rejected(
    client,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
    active_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-attendance",
        headers=auth_headers(token),
        json=attendance_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
            school_days=60,
            days_present=50,
            days_absent=5,
        ),
    )

    assert response.status_code == 422
