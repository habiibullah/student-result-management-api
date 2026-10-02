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


def test_admin_can_create_term_with_school_days(
    client,
    school_admin,
    academic_session_one,
):
    token = login(client, school_admin.email)

    response = client.post(
        "/api/terms",
        headers=auth_headers(token),
        json={
            "academic_session_id": academic_session_one.id,
            "name": "Third Term",
            "school_days": 62,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["academic_session_id"] == academic_session_one.id
    assert data["name"] == "Third Term"
    assert data["school_days"] == 62


def test_admin_can_create_term_without_school_days(
    client,
    school_admin,
    academic_session_one,
):
    token = login(client, school_admin.email)

    response = client.post(
        "/api/terms",
        headers=auth_headers(token),
        json={
            "academic_session_id": academic_session_one.id,
            "name": "Third Term",
        },
    )

    assert response.status_code == 201
    assert response.json()["school_days"] is None


def test_admin_can_update_term_school_days(
    client,
    school_admin,
    first_term,
):
    token = login(client, school_admin.email)

    response = client.patch(
        f"/api/terms/{first_term.id}",
        headers=auth_headers(token),
        json={
            "school_days": 64,
        },
    )

    assert response.status_code == 200
    assert response.json()["school_days"] == 64


def test_term_get_returns_school_days(
    client,
    db,
    school_admin,
    first_term,
):
    first_term.school_days = 61
    db.commit()
    db.refresh(first_term)

    token = login(client, school_admin.email)

    response = client.get(
        f"/api/terms/{first_term.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["school_days"] == 61


def test_term_list_returns_school_days(
    client,
    db,
    school_admin,
    first_term,
):
    first_term.school_days = 59
    db.commit()
    db.refresh(first_term)

    token = login(client, school_admin.email)

    response = client.get(
        "/api/terms",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    term = next(
        item
        for item in response.json()
        if item["id"] == first_term.id
    )

    assert term["school_days"] == 59


def test_create_term_rejects_zero_school_days(
    client,
    school_admin,
    academic_session_one,
):
    token = login(client, school_admin.email)

    response = client.post(
        "/api/terms",
        headers=auth_headers(token),
        json={
            "academic_session_id": academic_session_one.id,
            "name": "Third Term",
            "school_days": 0,
        },
    )

    assert response.status_code == 422


def test_create_term_rejects_negative_school_days(
    client,
    school_admin,
    academic_session_one,
):
    token = login(client, school_admin.email)

    response = client.post(
        "/api/terms",
        headers=auth_headers(token),
        json={
            "academic_session_id": academic_session_one.id,
            "name": "Third Term",
            "school_days": -1,
        },
    )

    assert response.status_code == 422


def test_update_term_rejects_zero_school_days(
    client,
    school_admin,
    first_term,
):
    token = login(client, school_admin.email)

    response = client.patch(
        f"/api/terms/{first_term.id}",
        headers=auth_headers(token),
        json={
            "school_days": 0,
        },
    )

    assert response.status_code == 422


def test_update_term_rejects_negative_school_days(
    client,
    school_admin,
    first_term,
):
    token = login(client, school_admin.email)

    response = client.patch(
        f"/api/terms/{first_term.id}",
        headers=auth_headers(token),
        json={
            "school_days": -5,
        },
    )

    assert response.status_code == 422
