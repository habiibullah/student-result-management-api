from app.models.assessment import Assessment
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


def create_assessment(
    db,
    class_id,
    subject_id,
    academic_session_id,
    term_id,
    name="Test CA",
):
    assessment = Assessment(
        class_id=class_id,
        subject_id=subject_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        assessment_type="CA",
        sequence=1,
        name=name,
        max_score=10,
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment


def create_score(
    db,
    student_id,
    assessment_id,
    score=8,
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


# ============================================================
# CREATE
# ============================================================


def test_active_subscription_allows_score_creation(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    active_term_assessment,
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
        "/api/student-scores",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "assessment_id": active_term_assessment.id,
            "score": 8,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["student_id"] == school_one_student.id
    assert data["assessment_id"] == active_term_assessment.id
    assert float(data["score"]) == 8.0


def test_pending_subscription_blocks_score_creation(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    second_term,
    pending_subscription,
):
    assessment = create_assessment(
        db=db,
        class_id=school_one_class.id,
        subject_id=school_one_subject.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
        name="Pending Term CA",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-scores",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "assessment_id": assessment.id,
            "score": 8,
        },
    )

    assert_subscription_required(response)


def test_cancelled_subscription_blocks_score_creation(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    third_term,
    cancelled_subscription,
):
    assessment = create_assessment(
        db=db,
        class_id=school_one_class.id,
        subject_id=school_one_subject.id,
        academic_session_id=academic_session_one.id,
        term_id=third_term.id,
        name="Cancelled Term CA",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-scores",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "assessment_id": assessment.id,
            "score": 8,
        },
    )

    assert_subscription_required(response)


def test_expired_subscription_blocks_score_creation(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    test_extra_term,
    expired_subscription,
):
    assessment = create_assessment(
        db=db,
        class_id=school_one_class.id,
        subject_id=school_one_subject.id,
        academic_session_id=academic_session_one.id,
        term_id=test_extra_term.id,
        name="Expired Term CA",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-scores",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "assessment_id": assessment.id,
            "score": 8,
        },
    )

    assert_subscription_required(response)


def test_missing_subscription_blocks_score_creation(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    unsubscribed_term,
):
    assessment = create_assessment(
        db=db,
        class_id=school_one_class.id,
        subject_id=school_one_subject.id,
        academic_session_id=academic_session_one.id,
        term_id=unsubscribed_term.id,
        name="Unsubscribed Term CA",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-scores",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "assessment_id": assessment.id,
            "score": 8,
        },
    )

    assert_subscription_required(response)


# ============================================================
# UPDATE
# ============================================================


def test_active_subscription_allows_score_update(
    client,
    db,
    school_admin,
    school_one_student,
    active_term_assessment,
    active_subscription,
):
    student_score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=7,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/student-scores/{student_score.id}",
        headers=auth_headers(token),
        json={
            "score": 9,
        },
    )

    assert response.status_code == 200
    assert float(response.json()["score"]) == 9.0


def test_inactive_subscription_blocks_score_update(
    client,
    db,
    school_admin,
    school_one_student,
    pending_term_assessment,
):
    student_score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=pending_term_assessment.id,
        score=7,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/student-scores/{student_score.id}",
        headers=auth_headers(token),
        json={
            "score": 9,
        },
    )

    assert_subscription_required(response)


# ============================================================
# DELETE
# ============================================================


def test_active_subscription_allows_score_delete(
    client,
    db,
    school_admin,
    school_one_student,
    active_term_assessment,
    active_subscription,
):
    student_score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=8,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/student-scores/{student_score.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204


def test_inactive_subscription_blocks_score_delete(
    client,
    db,
    school_admin,
    school_one_student,
    pending_term_assessment,
):
    student_score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=pending_term_assessment.id,
        score=8,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/student-scores/{student_score.id}",
        headers=auth_headers(token),
    )

    assert_subscription_required(response)


# ============================================================
# HISTORICAL READ ACCESS
# ============================================================


def test_historical_score_remains_readable_after_subscription_expires(
    client,
    db,
    school_admin,
    school_one_student,
    active_term_assessment,
    active_subscription,
):
    student_score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=8,
    )

    active_subscription.status = "expired"
    db.commit()

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/student-scores/{student_score.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == student_score.id


def test_historical_score_list_remains_available_after_subscription_expires(
    client,
    db,
    school_admin,
    school_one_student,
    active_term_assessment,
    active_subscription,
):
    student_score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=8,
    )

    active_subscription.status = "expired"
    db.commit()

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/student-scores",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        score["id"]
        for score in response.json()
    }

    assert student_score.id in returned_ids


# ============================================================
# TENANT ISOLATION
# ============================================================


def test_school_admin_cannot_read_other_school_score(
    client,
    db,
    school_admin,
    school_two_student,
    school_two_assessment,
):
    student_score = create_score(
        db=db,
        student_id=school_two_student.id,
        assessment_id=school_two_assessment.id,
        score=8,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/student-scores/{student_score.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student score not found"
    )


def test_school_admin_cannot_update_other_school_score(
    client,
    db,
    school_admin,
    school_two_student,
    school_two_assessment,
):
    student_score = create_score(
        db=db,
        student_id=school_two_student.id,
        assessment_id=school_two_assessment.id,
        score=8,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/student-scores/{student_score.id}",
        headers=auth_headers(token),
        json={
            "score": 9,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student score not found"
    )


def test_school_admin_cannot_delete_other_school_score(
    client,
    db,
    school_admin,
    school_two_student,
    school_two_assessment,
):
    student_score = create_score(
        db=db,
        student_id=school_two_student.id,
        assessment_id=school_two_assessment.id,
        score=8,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/student-scores/{student_score.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student score not found"
    )


def test_score_list_does_not_expose_other_school_records(
    client,
    db,
    school_admin,
    school_one_student,
    school_two_student,
    active_term_assessment,
    school_two_assessment,
):
    own_score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=8,
    )

    other_score = create_score(
        db=db,
        student_id=school_two_student.id,
        assessment_id=school_two_assessment.id,
        score=8,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/student-scores",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        score["id"]
        for score in response.json()
    }

    assert own_score.id in returned_ids
    assert other_score.id not in returned_ids
