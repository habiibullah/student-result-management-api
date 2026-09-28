from app.models import Class, ClassSubject, Subject


def login_headers(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def test_school_admin_can_create_class_subject_assignment(
    client,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
):
    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/class-subjects",
        headers=headers,
        json={
            "class_id": school_one_class.id,
            "subject_id": school_one_subject.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["class_id"] == school_one_class.id
    assert data["subject_id"] == school_one_subject.id
    assert (
        data["academic_session_id"]
        == academic_session_one.id
    )
    assert "id" in data
    assert "created_at" in data


def test_duplicate_class_subject_assignment_is_rejected(
    client,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
):
    headers = login_headers(
        client,
        school_admin.email,
    )

    payload = {
        "class_id": school_one_class.id,
        "subject_id": school_one_subject.id,
        "academic_session_id": academic_session_one.id,
    }

    first_response = client.post(
        "/api/class-subjects",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/class-subjects",
        headers=headers,
        json=payload,
    )

    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "This class-subject assignment already exists"
    )


def test_school_admin_can_bulk_assign_subjects(
    client,
    db,
    school_admin,
    school_one,
    school_one_class,
    school_one_subject,
    academic_session_one,
):
    mathematics = Subject(
        school_id=school_one.id,
        name="Mathematics",
        code="MTH",
        description="Mathematics",
    )
    english = Subject(
        school_id=school_one.id,
        name="English Language",
        code="ENG",
        description="English Language",
    )

    db.add_all([mathematics, english])
    db.commit()
    db.refresh(mathematics)
    db.refresh(english)

    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/class-subjects/bulk",
        headers=headers,
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "subject_ids": [
                school_one_subject.id,
                mathematics.id,
                english.id,
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert len(data) == 3

    returned_subject_ids = {
        assignment["subject_id"]
        for assignment in data
    }

    assert returned_subject_ids == {
        school_one_subject.id,
        mathematics.id,
        english.id,
    }


def test_bulk_assignment_rejects_existing_assignment_atomically(
    client,
    db,
    school_admin,
    school_one,
    school_one_class,
    school_one_subject,
    academic_session_one,
):
    mathematics = Subject(
        school_id=school_one.id,
        name="Mathematics",
        code="MTH",
    )

    db.add(mathematics)
    db.commit()
    db.refresh(mathematics)

    existing = ClassSubject(
        class_id=school_one_class.id,
        subject_id=school_one_subject.id,
        academic_session_id=academic_session_one.id,
    )

    db.add(existing)
    db.commit()

    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/class-subjects/bulk",
        headers=headers,
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "subject_ids": [
                school_one_subject.id,
                mathematics.id,
            ],
        },
    )

    assert response.status_code == 409

    mathematics_assignment = (
        db.query(ClassSubject)
        .filter(
            ClassSubject.class_id
            == school_one_class.id,
            ClassSubject.subject_id
            == mathematics.id,
            ClassSubject.academic_session_id
            == academic_session_one.id,
        )
        .first()
    )

    assert mathematics_assignment is None


def test_class_subjects_can_be_filtered_by_class_and_session(
    client,
    db,
    school_admin,
    school_one,
    school_one_class,
    school_one_subject,
    academic_session_one,
):
    second_class = Class(
        school_id=school_one.id,
        name="Junior Secondary Two",
        code="JSS2",
    )
    mathematics = Subject(
        school_id=school_one.id,
        name="Mathematics",
        code="MTH",
    )

    db.add_all([second_class, mathematics])
    db.commit()
    db.refresh(second_class)
    db.refresh(mathematics)

    db.add_all(
        [
            ClassSubject(
                class_id=school_one_class.id,
                subject_id=school_one_subject.id,
                academic_session_id=academic_session_one.id,
            ),
            ClassSubject(
                class_id=school_one_class.id,
                subject_id=mathematics.id,
                academic_session_id=academic_session_one.id,
            ),
            ClassSubject(
                class_id=second_class.id,
                subject_id=mathematics.id,
                academic_session_id=academic_session_one.id,
            ),
        ]
    )
    db.commit()

    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/class-subjects",
        headers=headers,
        params={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert {
        item["subject_id"]
        for item in data
    } == {
        school_one_subject.id,
        mathematics.id,
    }


def test_school_admin_cannot_assign_other_school_resources(
    client,
    school_admin,
    school_one_class,
    school_two_subject,
    academic_session_one,
):
    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/class-subjects",
        headers=headers,
        json={
            "class_id": school_one_class.id,
            "subject_id": school_two_subject.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Subject not found"


def test_bulk_assignment_rejects_other_school_subject(
    client,
    school_admin,
    school_one_class,
    school_one_subject,
    school_two_subject,
    academic_session_one,
):
    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/class-subjects/bulk",
        headers=headers,
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "subject_ids": [
                school_one_subject.id,
                school_two_subject.id,
            ],
        },
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "One or more subjects were not found"
    )


def test_class_subject_list_is_school_scoped(
    client,
    db,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
    school_two_class,
    school_two_subject,
    academic_session_two,
):
    db.add_all(
        [
            ClassSubject(
                class_id=school_one_class.id,
                subject_id=school_one_subject.id,
                academic_session_id=academic_session_one.id,
            ),
            ClassSubject(
                class_id=school_two_class.id,
                subject_id=school_two_subject.id,
                academic_session_id=academic_session_two.id,
            ),
        ]
    )
    db.commit()

    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/class-subjects",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["class_id"] == school_one_class.id
    assert data[0]["subject_id"] == school_one_subject.id


def test_school_admin_can_delete_class_subject_assignment(
    client,
    db,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
):
    assignment = ClassSubject(
        class_id=school_one_class.id,
        subject_id=school_one_subject.id,
        academic_session_id=academic_session_one.id,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    assignment_id = assignment.id

    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/class-subjects/{assignment_id}",
        headers=headers,
    )

    assert response.status_code == 204

    db.expire_all()

    assert db.get(ClassSubject, assignment_id) is None


def test_school_admin_cannot_delete_other_school_assignment(
    client,
    db,
    school_admin,
    school_two_class,
    school_two_subject,
    academic_session_two,
):
    assignment = ClassSubject(
        class_id=school_two_class.id,
        subject_id=school_two_subject.id,
        academic_session_id=academic_session_two.id,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    assignment_id = assignment.id

    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/class-subjects/{assignment_id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Class-subject assignment not found"
    )

    assert db.get(ClassSubject, assignment_id) is not None


def test_invalid_class_subject_ids_are_rejected(
    client,
    school_admin,
):
    headers = login_headers(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/class-subjects",
        headers=headers,
        json={
            "class_id": 0,
            "subject_id": -1,
            "academic_session_id": 0,
        },
    )

    assert response.status_code == 422


def test_bulk_assignment_requires_unique_positive_subject_ids(
    client,
    school_admin,
):
    headers = login_headers(
        client,
        school_admin.email,
    )

    duplicate_response = client.post(
        "/api/class-subjects/bulk",
        headers=headers,
        json={
            "class_id": 1,
            "academic_session_id": 1,
            "subject_ids": [1, 1],
        },
    )

    assert duplicate_response.status_code == 422

    invalid_response = client.post(
        "/api/class-subjects/bulk",
        headers=headers,
        json={
            "class_id": 1,
            "academic_session_id": 1,
            "subject_ids": [1, 0],
        },
    )

    assert invalid_response.status_code == 422

    empty_response = client.post(
        "/api/class-subjects/bulk",
        headers=headers,
        json={
            "class_id": 1,
            "academic_session_id": 1,
            "subject_ids": [],
        },
    )

    assert empty_response.status_code == 422
