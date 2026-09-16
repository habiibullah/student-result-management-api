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


def test_platform_admin_can_list_all_schools(
    client,
    platform_admin,
    school_one,
    school_two,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.get(
        "/api/schools",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["id"] == school_one.id
    assert data[0]["name"] == school_one.name
    assert data[0]["slug"] == school_one.slug
    assert data[0]["email"] == school_one.email
    assert data[0]["is_active"] is True

    assert data[1]["id"] == school_two.id
    assert data[1]["name"] == school_two.name
    assert data[1]["slug"] == school_two.slug
    assert data[1]["email"] == school_two.email
    assert data[1]["is_active"] is True


def test_school_admin_cannot_list_all_schools(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/schools",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_schools(
    client,
):
    response = client.get(
        "/api/schools",
    )

    assert response.status_code == 401


def test_platform_admin_school_list_returns_empty_list(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.get(
        "/api/schools",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_school_list_contains_school_response_fields(
    client,
    platform_admin,
    school_one,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.get(
        "/api/schools",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    school = data[0]

    expected_fields = {
        "id",
        "name",
        "slug",
        "email",
        "phone",
        "address",
        "motto",
        "logo_url",
        "is_active",
        "created_at",
        "updated_at",
    }

    assert set(school.keys()) == expected_fields

    assert school["id"] == school_one.id
    assert school["name"] == "Test School One"
    assert school["slug"] == "test-school-one"
    assert school["email"] == "school.one@example.com"
    assert school["is_active"] is True


def school_registration_payload():
    return {
        "school_name": "Bright Future Academy",
        "school_slug": "bright-future-academy",
        "school_email": "info@brightfuture.example.com",
        "phone": "+2348000000000",
        "address": "Osun State, Nigeria",
        "motto": "Knowledge and Excellence",
        "admin_email": "admin@brightfuture.example.com",
        "admin_password": "SecurePassword123!",
    }


def test_platform_admin_can_register_school(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.post(
        "/api/schools/register",
        json=school_registration_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["school_name"] == "Bright Future Academy"
    assert data["school_slug"] == "bright-future-academy"
    assert data["school_email"] == "info@brightfuture.example.com"
    assert data["admin_email"] == "admin@brightfuture.example.com"
    assert data["role"] == "admin"
    assert data["message"] == "School registered successfully"


def test_school_admin_cannot_register_school(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/schools/register",
        json=school_registration_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_register_school(
    client,
):
    response = client.post(
        "/api/schools/register",
        json=school_registration_payload(),
    )

    assert response.status_code == 401


def test_platform_admin_cannot_register_duplicate_school_slug(
    client,
    platform_admin,
    school_one,
):
    token = login(
        client,
        platform_admin.email,
    )

    payload = school_registration_payload()
    payload["school_slug"] = school_one.slug

    response = client.post(
        "/api/schools/register",
        json=payload,
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A school with this slug already exists"
    )


def test_platform_admin_cannot_register_duplicate_admin_email(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    payload = school_registration_payload()
    payload["admin_email"] = platform_admin.email

    response = client.post(
        "/api/schools/register",
        json=payload,
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "A user with this email already exists"
    )
