from app.models.enrollment import Enrollment
from app.models.student_behavioural_assessment import (
    StudentBehaviouralAssessment,
)


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


def behavioural_payload(
    student_id,
    academic_session_id,
    term_id,
    punctuality=5,
    neatness=4,
    honesty=5,
    politeness=4,
    attentiveness=5,
    cooperation=4,
):
    return {
        "student_id": student_id,
        "academic_session_id": academic_session_id,
        "term_id": term_id,
        "punctuality": punctuality,
        "neatness": neatness,
        "honesty": honesty,
        "politeness": politeness,
        "attentiveness": attentiveness,
        "cooperation": cooperation,
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


def create_behavioural_assessment(
    db,
    student_id,
    academic_session_id,
    term_id,
    punctuality=5,
    neatness=4,
    honesty=5,
    politeness=4,
    attentiveness=5,
    cooperation=4,
):
    assessment = StudentBehaviouralAssessment(
        student_id=student_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        punctuality=punctuality,
        neatness=neatness,
        honesty=honesty,
        politeness=politeness,
        attentiveness=attentiveness,
        cooperation=cooperation,
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment

# ============================================================
# CREATE
# ============================================================


def test_active_subscription_allows_behavioural_creation(
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
        "/api/student-behavioural-assessments",
        headers=auth_headers(token),
        json=behavioural_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["student_id"] == school_one_student.id
    assert data["academic_session_id"] == academic_session_one.id
    assert data["term_id"] == first_term.id
    assert data["punctuality"] == 5
    assert data["neatness"] == 4
    assert data["honesty"] == 5
    assert data["politeness"] == 4
    assert data["attentiveness"] == 5
    assert data["cooperation"] == 4


def test_behavioural_rating_below_one_is_rejected(
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
        "/api/student-behavioural-assessments",
        headers=auth_headers(token),
        json=behavioural_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
            punctuality=0,
        ),
    )

    assert response.status_code == 422


def test_behavioural_rating_above_five_is_rejected(
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
        "/api/student-behavioural-assessments",
        headers=auth_headers(token),
        json=behavioural_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
            cooperation=6,
        ),
    )

    assert response.status_code == 422

def test_duplicate_behavioural_assessment_is_rejected(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
    active_subscription,
    school_one_class,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    create_behavioural_assessment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/student-behavioural-assessments",
        headers=auth_headers(token),
        json=behavioural_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        ),

    )


    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Behavioural assessment already exists for "
        "this student, session and term"
    )

# ============================================================
# UPDATE
# ============================================================


def test_active_subscription_allows_behavioural_update(
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

    assessment = create_behavioural_assessment(
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
            "/api/student-behavioural-assessments/"
            f"{assessment.id}"
        ),
        headers=auth_headers(token),
        json={
            "punctuality": 4,
            "neatness": 5,
            "honesty": 3,
            "politeness": 5,
            "attentiveness": 4,
            "cooperation": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["punctuality"] == 4
    assert data["neatness"] == 5
    assert data["honesty"] == 3
    assert data["politeness"] == 5
    assert data["attentiveness"] == 4
    assert data["cooperation"] == 5


# ============================================================
# DELETE
# ============================================================


def test_active_subscription_allows_behavioural_delete(
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

    assessment = create_behavioural_assessment(
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
            "/api/student-behavioural-assessments/"
            f"{assessment.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 204

# ============================================================
# SUBSCRIPTION PROTECTION
# ============================================================


def test_inactive_subscription_blocks_behavioural_creation(
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
        "/api/student-behavioural-assessments",
        headers=auth_headers(token),
        json=behavioural_payload(
            student_id=school_one_student.id,
            academic_session_id=academic_session_one.id,
            term_id=second_term.id,
        ),
    )

    assert_subscription_required(response)

# ============================================================
# HISTORICAL READ ACCESS
# ============================================================


def test_historical_behavioural_assessment_remains_readable(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
    active_subscription,
):
    assessment = create_behavioural_assessment(
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
            "/api/student-behavioural-assessments/"
            f"{assessment.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == assessment.id
    assert data["student_id"] == school_one_student.id
    assert data["punctuality"] == 5
    assert data["neatness"] == 4
    assert data["honesty"] == 5
    assert data["politeness"] == 4
    assert data["attentiveness"] == 5
    assert data["cooperation"] == 4

def test_school_admin_cannot_read_other_school_behavioural_assessment(
    client,
    db,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
    school_two_subscription,
):
    behavioural = create_behavioural_assessment(
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
            "/api/student-behavioural-assessments/"
            f"{behavioural.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Behavioural assessment not found"
    )

def test_school_admin_cannot_update_other_school_behavioural_assessment(
    client,
    db,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
    school_two_subscription,
):
    behavioural = create_behavioural_assessment(
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
            "/api/student-behavioural-assessments/"
            f"{behavioural.id}"
        ),
        headers=auth_headers(token),
        json={
            "punctuality": 3,
            "neatness": 3,
            "honesty": 3,
            "politeness": 3,
            "attentiveness": 3,
            "cooperation": 3,
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Behavioural assessment not found"
    )

def test_school_admin_cannot_delete_other_school_behavioural_assessment(
    client,
    db,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
    school_two_subscription,
):
    behavioural = create_behavioural_assessment(
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
            "/api/student-behavioural-assessments/"
            f"{behavioural.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Behavioural assessment not found"
    )

def test_behavioural_list_does_not_expose_other_school_records(
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
    own_behavioural = create_behavioural_assessment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    other_behavioural = create_behavioural_assessment(
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
        "/api/student-behavioural-assessments",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        record["id"]
        for record in response.json()
    }

    assert own_behavioural.id in returned_ids
    assert other_behavioural.id not in returned_ids


# ============================================================
# ADDITIONAL SUBSCRIPTION / TENANT PROTECTION
# ============================================================


def test_inactive_subscription_blocks_behavioural_update(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    second_term,
    pending_subscription,
):
    assessment = create_behavioural_assessment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
    )

    token = login(client, school_admin.email)

    response = client.patch(
        f"/api/student-behavioural-assessments/{assessment.id}",
        headers=auth_headers(token),
        json={"punctuality": 3},
    )

    assert_subscription_required(response)


def test_inactive_subscription_blocks_behavioural_delete(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    second_term,
    pending_subscription,
):
    assessment = create_behavioural_assessment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
    )

    token = login(client, school_admin.email)

    response = client.delete(
        f"/api/student-behavioural-assessments/{assessment.id}",
        headers=auth_headers(token),
    )

    assert_subscription_required(response)


def test_school_admin_cannot_create_behavioural_for_other_school_student(
    client,
    school_admin,
    school_two_student,
    academic_session_two,
    school_two_term,
    school_two_subscription,
):
    token = login(client, school_admin.email)

    response = client.post(
        "/api/student-behavioural-assessments",
        headers=auth_headers(token),
        json=behavioural_payload(
            student_id=school_two_student.id,
            academic_session_id=academic_session_two.id,
            term_id=school_two_term.id,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"
