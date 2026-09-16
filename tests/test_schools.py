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


def test_platform_admin_can_get_school_by_id(
    client,
    platform_admin,
    school_one,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.get(
        f"/api/schools/{school_one.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == school_one.id
    assert data["name"] == school_one.name
    assert data["slug"] == school_one.slug
    assert data["email"] == school_one.email
    assert data["is_active"] is True


def test_school_admin_cannot_get_school_by_id(
    client,
    school_admin,
    school_one,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/schools/{school_one.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_get_school_by_id(
    client,
    school_one,
):
    response = client.get(
        f"/api/schools/{school_one.id}",
    )

    assert response.status_code == 401


def test_platform_admin_get_school_returns_404_for_unknown_school(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.get(
        "/api/schools/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"

def test_platform_admin_can_update_school_by_id(
    client,
    platform_admin,
    school_one,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        f"/api/schools/{school_one.id}",
        json={
            "name": "Updated School Name",
            "email": "updated@example.com",
            "phone": "+2348111111111",
            "address": "Updated Address",
            "motto": "Updated Motto",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == school_one.id
    assert data["name"] == "Updated School Name"
    assert data["email"] == "updated@example.com"
    assert data["phone"] == "+2348111111111"
    assert data["address"] == "Updated Address"
    assert data["motto"] == "Updated Motto"


def test_platform_admin_can_partially_update_school(
    client,
    platform_admin,
    school_one,
):
    token = login(
        client,
        platform_admin.email,
    )

    original_email = school_one.email

    response = client.patch(
        f"/api/schools/{school_one.id}",
        json={
            "name": "Renamed School",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Renamed School"
    assert data["email"] == original_email


def test_school_admin_cannot_update_school_by_id(
    client,
    school_admin,
    school_one,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/schools/{school_one.id}",
        json={
            "name": "Unauthorized Change",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_update_school_by_id(
    client,
    school_one,
):
    response = client.patch(
        f"/api/schools/{school_one.id}",
        json={
            "name": "Unauthorized Change",
        },
    )

    assert response.status_code == 401


def test_platform_admin_update_school_returns_404_for_unknown_school(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        "/api/schools/999999",
        json={
            "name": "Unknown School",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"


def test_platform_admin_can_deactivate_school(
    client,
    platform_admin,
    school_one,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        f"/api/schools/{school_one.id}/status",
        json={
            "is_active": False,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == school_one.id
    assert data["is_active"] is False


def test_platform_admin_can_reactivate_school(
    client,
    platform_admin,
    school_one,
):
    school_one.is_active = False

    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        f"/api/schools/{school_one.id}/status",
        json={
            "is_active": True,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == school_one.id
    assert data["is_active"] is True


def test_school_admin_cannot_change_school_status(
    client,
    school_admin,
    school_one,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/schools/{school_one.id}/status",
        json={
            "is_active": False,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_change_school_status(
    client,
    school_one,
):
    response = client.patch(
        f"/api/schools/{school_one.id}/status",
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 401


def test_change_school_status_returns_404_for_unknown_school(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        "/api/schools/999999/status",
        json={
            "is_active": False,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found"
