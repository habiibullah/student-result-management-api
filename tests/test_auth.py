def test_login_success(client, platform_admin):
    response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, platform_admin):
    response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid email or password"
    )


def test_login_unknown_user(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "does.not.exist@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid email or password"
    )


def test_inactive_user_cannot_login(
    client,
    inactive_platform_admin,
):
    response = client.post(
        "/api/auth/login",
        json={
            "email": inactive_platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "User account is inactive"
    )


def test_protected_endpoint_without_token(client):
    response = client.get(
        "/api/users/me"
    )

    assert response.status_code == 401


def test_protected_endpoint_with_invalid_token(client):
    response = client.get(
        "/api/users/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid authentication token"
    )


def test_current_platform_admin(client, platform_admin):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/users/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == platform_admin.id
    assert data["email"] == platform_admin.email
    assert data["role"] == "admin"
    assert data["account_type"] == "platform_admin"
    assert data["school_id"] is None
    assert data["is_active"] is True
