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
