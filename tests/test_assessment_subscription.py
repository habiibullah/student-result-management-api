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


def assessment_payload(
    class_id,
    subject_id,
    academic_session_id,
    term_id,
    sequence=1,
    name="Continuous Assessment One",
):
    return {
        "class_id": class_id,
        "subject_id": subject_id,
        "academic_session_id": academic_session_id,
        "term_id": term_id,
        "assessment_type": "CA",
        "sequence": sequence,
        "name": name,
        "max_score": 10,
    }


def assert_subscription_required(response):
    assert response.status_code == 403

    assert response.json()["detail"] == (
        "An active subscription is required "
        "for this academic term"
    )


# ============================================================
# CREATE
# ============================================================


def test_active_subscription_allows_assessment_creation(
    client,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
    active_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/assessments",
        headers=auth_headers(token),
        json=assessment_payload(
            class_id=school_one_class.id,
            subject_id=school_one_subject.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["class_id"] == school_one_class.id
    assert data["subject_id"] == school_one_subject.id
    assert data["academic_session_id"] == (
        academic_session_one.id
    )
    assert data["term_id"] == first_term.id
    assert data["assessment_type"] == "CA"
    assert data["sequence"] == 1
    assert data["max_score"] == 10


def test_pending_subscription_blocks_assessment_creation(
    client,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
    second_term,
    pending_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/assessments",
        headers=auth_headers(token),
        json=assessment_payload(
            class_id=school_one_class.id,
            subject_id=school_one_subject.id,
            academic_session_id=academic_session_one.id,
            term_id=second_term.id,
        ),
    )

    assert_subscription_required(response)


def test_cancelled_subscription_blocks_assessment_creation(
    client,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
    third_term,
    cancelled_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/assessments",
        headers=auth_headers(token),
        json=assessment_payload(
            class_id=school_one_class.id,
            subject_id=school_one_subject.id,
            academic_session_id=academic_session_one.id,
            term_id=third_term.id,
        ),
    )

    assert_subscription_required(response)


def test_expired_subscription_blocks_assessment_creation(
    client,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
    test_extra_term,
    expired_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/assessments",
        headers=auth_headers(token),
        json=assessment_payload(
            class_id=school_one_class.id,
            subject_id=school_one_subject.id,
            academic_session_id=academic_session_one.id,
            term_id=test_extra_term.id,
        ),
    )

    assert_subscription_required(response)


def test_missing_subscription_blocks_assessment_creation(
    client,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
    unsubscribed_term,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/assessments",
        headers=auth_headers(token),
        json=assessment_payload(
            class_id=school_one_class.id,
            subject_id=school_one_subject.id,
            academic_session_id=academic_session_one.id,
            term_id=unsubscribed_term.id,
        ),
    )

    assert_subscription_required(response)


# ============================================================
# UPDATE
# ============================================================


def test_active_subscription_allows_assessment_update(
    client,
    school_admin,
    active_term_assessment,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            "/api/assessments/"
            f"{active_term_assessment.id}"
        ),
        headers=auth_headers(token),
        json={
            "name": "Updated First CA",
        },
    )

    assert response.status_code == 200

    assert response.json()["name"] == (
        "Updated First CA"
    )


def test_inactive_subscription_blocks_assessment_update(
    client,
    school_admin,
    pending_term_assessment,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            "/api/assessments/"
            f"{pending_term_assessment.id}"
        ),
        headers=auth_headers(token),
        json={
            "name": "Unauthorized Update",
        },
    )

    assert_subscription_required(response)


# ============================================================
# DELETE
# ============================================================


def test_active_subscription_allows_assessment_delete(
    client,
    school_admin,
    active_term_assessment,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        (
            "/api/assessments/"
            f"{active_term_assessment.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 204


def test_inactive_subscription_blocks_assessment_delete(
    client,
    school_admin,
    pending_term_assessment,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        (
            "/api/assessments/"
            f"{pending_term_assessment.id}"
        ),
        headers=auth_headers(token),
    )

    assert_subscription_required(response)


# ============================================================
# HISTORICAL READ ACCESS
# ============================================================


def test_historical_assessment_remains_readable_after_subscription_expires(
    client,
    db,
    school_admin,
    active_term_assessment,
    active_subscription,
):
    active_subscription.status = "expired"

    db.commit()
    db.refresh(active_subscription)

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        (
            "/api/assessments/"
            f"{active_term_assessment.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == active_term_assessment.id
    assert data["name"] == active_term_assessment.name


def test_historical_assessment_list_remains_available_after_subscription_expires(
    client,
    db,
    school_admin,
    active_term_assessment,
    active_subscription,
):
    active_subscription.status = "expired"

    db.commit()
    db.refresh(active_subscription)

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/assessments",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        assessment["id"]
        for assessment in response.json()
    }

    assert active_term_assessment.id in returned_ids


# ============================================================
# TENANT ISOLATION
# ============================================================


def test_school_admin_cannot_read_other_school_assessment(
    client,
    school_admin,
    school_two_assessment,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        (
            "/api/assessments/"
            f"{school_two_assessment.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Assessment not found"
    )


def test_school_admin_cannot_update_other_school_assessment(
    client,
    school_admin,
    school_two_assessment,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            "/api/assessments/"
            f"{school_two_assessment.id}"
        ),
        headers=auth_headers(token),
        json={
            "name": "Cross School Change",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Assessment not found"
    )


def test_school_admin_cannot_delete_other_school_assessment(
    client,
    school_admin,
    school_two_assessment,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        (
            "/api/assessments/"
            f"{school_two_assessment.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Assessment not found"
    )


def test_assessment_list_does_not_expose_other_school_records(
    client,
    school_admin,
    active_term_assessment,
    school_two_assessment,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/assessments",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        assessment["id"]
        for assessment in response.json()
    }

    assert active_term_assessment.id in returned_ids
    assert school_two_assessment.id not in returned_ids
