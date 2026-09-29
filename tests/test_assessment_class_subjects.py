from app.models import AcademicSession, Class, ClassSubject


def login_headers(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    return {
        "Authorization": f"Bearer {response.json()['access_token']}",
    }


def assessment_payload(
    class_id,
    subject_id,
    academic_session_id,
    term_id,
):
    return {
        "class_id": class_id,
        "subject_id": subject_id,
        "academic_session_id": academic_session_id,
        "term_id": term_id,
        "assessment_type": "CA",
        "sequence": 1,
        "name": "Continuous Assessment One",
        "max_score": 20,
    }


def create_class_subject(
    db,
    class_id,
    subject_id,
    academic_session_id,
):
    assignment = ClassSubject(
        class_id=class_id,
        subject_id=subject_id,
        academic_session_id=academic_session_id,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def test_assigned_subject_allows_assessment_creation(
    client,
    db,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_class_subject(
        db,
        school_one_class.id,
        school_one_subject.id,
        academic_session_one.id,
    )

    response = client.post(
        "/api/assessments",
        headers=login_headers(client, school_admin.email),
        json=assessment_payload(
            school_one_class.id,
            school_one_subject.id,
            academic_session_one.id,
            first_term.id,
        ),
    )

    assert response.status_code == 201, response.text


def test_unassigned_subject_rejects_assessment_creation(
    client,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
    active_subscription,
):
    response = client.post(
        "/api/assessments",
        headers=login_headers(client, school_admin.email),
        json=assessment_payload(
            school_one_class.id,
            school_one_subject.id,
            academic_session_one.id,
            first_term.id,
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Subject is not assigned to this class "
        "for the selected academic session"
    )


def test_assignment_for_different_class_does_not_allow_assessment(
    client,
    db,
    school_admin,
    school_one,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
    active_subscription,
):
    other_class = Class(
        school_id=school_one.id,
        name="Other Class",
        code="OTHER",
    )
    db.add(other_class)
    db.commit()
    db.refresh(other_class)

    create_class_subject(
        db,
        other_class.id,
        school_one_subject.id,
        academic_session_one.id,
    )

    response = client.post(
        "/api/assessments",
        headers=login_headers(client, school_admin.email),
        json=assessment_payload(
            school_one_class.id,
            school_one_subject.id,
            academic_session_one.id,
            first_term.id,
        ),
    )

    assert response.status_code == 400


def test_assignment_for_different_session_does_not_allow_assessment(
    client,
    db,
    school_admin,
    school_one,
    school_one_class,
    school_one_subject,
    academic_session_one,
    first_term,
    active_subscription,
):
    other_session = AcademicSession(
        school_id=school_one.id,
        name="2027/2028",
        is_current=False,
    )
    db.add(other_session)
    db.commit()
    db.refresh(other_session)

    create_class_subject(
        db,
        school_one_class.id,
        school_one_subject.id,
        other_session.id,
    )

    response = client.post(
        "/api/assessments",
        headers=login_headers(client, school_admin.email),
        json=assessment_payload(
            school_one_class.id,
            school_one_subject.id,
            academic_session_one.id,
            first_term.id,
        ),
    )

    assert response.status_code == 400