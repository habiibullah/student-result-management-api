from app.models.enrollment import Enrollment
from app.models.term_report_comment import TermReportComment


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


def create_comment(
    db,
    student_id,
    academic_session_id,
    term_id,
):
    comment = TermReportComment(
        student_id=student_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        teacher_comment="Good academic performance.",
        principal_comment="Keep up the good work.",
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


def comment_payload(
    student_id,
    academic_session_id,
    term_id,
):
    return {
        "student_id": student_id,
        "academic_session_id": academic_session_id,
        "term_id": term_id,
        "teacher_comment": (
            "Good academic performance."
        ),
        "principal_comment": (
            "Keep up the good work."
        ),
    }


# ============================================================
# CREATE
# ============================================================


def test_active_subscription_allows_comment_creation(
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
        "/api/term-report-comments",
        headers=auth_headers(token),
        json=comment_payload(
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
    assert data["teacher_comment"] == (
        "Good academic performance."
    )


def test_pending_subscription_blocks_comment_creation(
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
        "/api/term-report-comments",
        headers=auth_headers(token),
        json=comment_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=second_term.id,
        ),
    )

    assert_subscription_required(response)


def test_cancelled_subscription_blocks_comment_creation(
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
        "/api/term-report-comments",
        headers=auth_headers(token),
        json=comment_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=third_term.id,
        ),
    )

    assert_subscription_required(response)


def test_expired_subscription_blocks_comment_creation(
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
        "/api/term-report-comments",
        headers=auth_headers(token),
        json=comment_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=test_extra_term.id,
        ),
    )

    assert_subscription_required(response)


def test_missing_subscription_blocks_comment_creation(
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
        "/api/term-report-comments",
        headers=auth_headers(token),
        json=comment_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=unsubscribed_term.id,
        ),
    )

    assert_subscription_required(response)


# ============================================================
# UPDATE
# ============================================================


def test_active_subscription_allows_comment_update(
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

    comment = create_comment(
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
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
        json={
            "teacher_comment": (
                "Excellent improvement this term."
            ),
        },
    )

    assert response.status_code == 200

    assert response.json()["teacher_comment"] == (
        "Excellent improvement this term."
    )


def test_inactive_subscription_blocks_comment_update(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    second_term,
    pending_subscription,
):
    comment = create_comment(
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
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
        json={
            "teacher_comment": (
                "This change must be blocked."
            ),
        },
    )

    assert_subscription_required(response)


# ============================================================
# DELETE
# ============================================================


def test_active_subscription_allows_comment_delete(
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

    comment = create_comment(
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
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204


def test_inactive_subscription_blocks_comment_delete(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    second_term,
    pending_subscription,
):
    comment = create_comment(
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
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
    )

    assert_subscription_required(response)


# ============================================================
# HISTORICAL READ ACCESS
# ============================================================


def test_historical_comment_remains_readable_after_subscription_expires(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
    active_subscription,
):
    comment = create_comment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    active_subscription.status = "expired"
    db.commit()

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == comment.id


def test_historical_comment_list_remains_available_after_subscription_expires(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
    active_subscription,
):
    comment = create_comment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    active_subscription.status = "expired"
    db.commit()

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/term-report-comments",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        item["id"]
        for item in response.json()
    }

    assert comment.id in returned_ids


# ============================================================
# TENANT ISOLATION
# ============================================================


def test_school_admin_cannot_read_other_school_comment(
    client,
    db,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
):
    comment = create_comment(
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
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Report comment not found"
    )


def test_school_admin_cannot_update_other_school_comment(
    client,
    db,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
):
    comment = create_comment(
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
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
        json={
            "teacher_comment": "Cross-school update",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Report comment not found"
    )


def test_school_admin_cannot_delete_other_school_comment(
    client,
    db,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
):
    comment = create_comment(
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
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Report comment not found"
    )


def test_comment_list_does_not_expose_other_school_records(
    client,
    db,
    school_admin,
    school_one_student,
    school_two_student,
    academic_session_one,
    academic_session_two,
    first_term,
    school_two_term,
):
    own_comment = create_comment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    other_comment = create_comment(
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
        "/api/term-report-comments",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        item["id"]
        for item in response.json()
    }

    assert own_comment.id in returned_ids
    assert other_comment.id not in returned_ids
