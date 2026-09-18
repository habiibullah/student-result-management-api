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

def test_authenticated_user_can_change_password(
    client,
    platform_admin,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "TestPassword123!",
            "new_password": "NewPassword456!",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Password changed successfully"
    )

    old_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "NewPassword456!",
        },
    )

    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password(
    client,
    platform_admin,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword456!",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Current password is incorrect"
    )


def test_change_password_rejects_same_password(
    client,
    platform_admin,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "TestPassword123!",
            "new_password": "TestPassword123!",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "New password must be different from current password"
    )


def test_change_password_requires_authentication(client):
    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "TestPassword123!",
            "new_password": "NewPassword456!",
        },
    )

    assert response.status_code == 401


def test_change_password_rejects_short_new_password(
    client,
    platform_admin,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "TestPassword123!",
            "new_password": "short",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422

def test_failed_change_password_preserves_existing_password(
    client,
    platform_admin,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword456!",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400

    original_password_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert original_password_login.status_code == 200

    rejected_password_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "NewPassword456!",
        },
    )

    assert rejected_password_login.status_code == 401
