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

def test_login_reports_password_change_required(
    client,
    db,
    platform_admin,
):
    platform_admin.must_change_password = True
    db.commit()

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
    assert data["must_change_password"] is True


def test_normal_login_reports_password_change_not_required(
    client,
    platform_admin,
):
    response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["must_change_password"]
        is False
    )


def test_user_requiring_password_change_cannot_access_normal_route(
    client,
    db,
    platform_admin,
):
    platform_admin.must_change_password = True
    db.commit()

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
        "/api/schools",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Password change required"
    )


def test_user_requiring_password_change_can_change_password(
    client,
    db,
    platform_admin,
):
    platform_admin.must_change_password = True
    db.commit()

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
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "current_password": "TestPassword123!",
            "new_password": "PrivatePassword456!",
        },
    )

    assert response.status_code == 200

    db.refresh(platform_admin)

    assert platform_admin.must_change_password is False


def test_forced_password_change_requires_new_login_for_access(
    client,
    db,
    platform_admin,
):
    platform_admin.must_change_password = True
    db.commit()

    temporary_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )
    assert temporary_login.status_code == 200

    old_token = temporary_login.json()["access_token"]

    # Normal access is blocked while a password change
    # is required.
    blocked_response = client.get(
        "/api/schools",
        headers={"Authorization": f"Bearer {old_token}"},
    )

    assert blocked_response.status_code == 403
    assert blocked_response.json()["detail"] == (
        "Password change required"
    )

    # The flagged user can still change the password.
    change_response = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {old_token}"},
        json={
            "current_password": "TestPassword123!",
            "new_password": "PrivatePassword456!",
        },
    )

    assert change_response.status_code == 200

    db.refresh(platform_admin)
    assert platform_admin.must_change_password is False

    # Changing the password increments token_version,
    # so the token used for the change is now revoked.
    revoked_response = client.get(
        "/api/schools",
        headers={"Authorization": f"Bearer {old_token}"},
    )

    assert revoked_response.status_code == 401
    assert revoked_response.json()["detail"] == (
        "Token has been revoked"
    )

    # The user must authenticate with the new password.
    new_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "PrivatePassword456!",
        },
    )

    assert new_login.status_code == 200
    assert new_login.json()["must_change_password"] is False

    new_token = new_login.json()["access_token"]

    # A newly issued token carries the current
    # token_version and restores normal access.
    restored_response = client.get(
        "/api/schools",
        headers={"Authorization": f"Bearer {new_token}"},
    )

    assert restored_response.status_code == 200

def test_failed_forced_password_change_preserves_requirement(
    client,
    db,
    platform_admin,
):
    platform_admin.must_change_password = True
    db.commit()

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
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "current_password": "WrongPassword123!",
            "new_password": "PrivatePassword456!",
        },
    )

    assert response.status_code == 400

    db.refresh(platform_admin)

    assert platform_admin.must_change_password is True

    blocked_response = client.get(
        "/api/schools",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert blocked_response.status_code == 403
    assert blocked_response.json()["detail"] == (
        "Password change required"
    )

def test_password_change_invalidates_previously_issued_token(
    client,
    platform_admin,
):
    first_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )
    assert first_login.status_code == 200
    old_token = first_login.json()["access_token"]

    change_response = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {old_token}"},
        json={
            "current_password": "TestPassword123!",
            "new_password": "PrivatePassword456!",
        },
    )
    assert change_response.status_code == 200

    old_token_response = client.get(
        "/api/schools",
        headers={"Authorization": f"Bearer {old_token}"},
    )

    assert old_token_response.status_code == 401
    assert old_token_response.json()["detail"] == (
        "Token has been revoked"
    )


def test_new_login_after_password_change_receives_valid_token(
    client,
    platform_admin,
):
    first_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )
    assert first_login.status_code == 200
    old_token = first_login.json()["access_token"]

    change_response = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {old_token}"},
        json={
            "current_password": "TestPassword123!",
            "new_password": "PrivatePassword456!",
        },
    )
    assert change_response.status_code == 200

    second_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "PrivatePassword456!",
        },
    )

    assert second_login.status_code == 200

    new_token = second_login.json()["access_token"]

    protected_response = client.get(
        "/api/schools",
        headers={"Authorization": f"Bearer {new_token}"},
    )

    assert protected_response.status_code == 200


def test_admin_password_reset_invalidates_existing_target_token(
    client,
    platform_admin,
    school_admin,
):
    school_admin_login = client.post(
        "/api/auth/login",
        json={
            "email": school_admin.email,
            "password": "TestPassword123!",
        },
    )
    assert school_admin_login.status_code == 200
    old_school_admin_token = (
        school_admin_login.json()["access_token"]
    )

    platform_admin_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )
    assert platform_admin_login.status_code == 200
    platform_admin_token = (
        platform_admin_login.json()["access_token"]
    )

    reset_response = client.post(
        (
            "/api/admin-management/users/"
            f"{school_admin.id}/reset-password"
        ),
        headers={
            "Authorization": f"Bearer {platform_admin_token}",
        },
        json={
            "temporary_password": "TemporaryPassword123!",
        },
    )

    assert reset_response.status_code == 200

    old_token_response = client.get(
        "/api/classes",
        headers={
            "Authorization": (
                f"Bearer {old_school_admin_token}"
            ),
        },
    )

    assert old_token_response.status_code == 401
    assert old_token_response.json()["detail"] == (
        "Token has been revoked"
    )


def test_unrelated_users_token_remains_valid_after_password_reset(
    client,
    platform_admin,
    school_admin,
):
    platform_admin_login = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )
    assert platform_admin_login.status_code == 200

    platform_admin_token = (
        platform_admin_login.json()["access_token"]
    )

    reset_response = client.post(
        (
            "/api/admin-management/users/"
            f"{school_admin.id}/reset-password"
        ),
        headers={
            "Authorization": f"Bearer {platform_admin_token}",
        },
        json={
            "temporary_password": "TemporaryPassword123!",
        },
    )

    assert reset_response.status_code == 200

    # Resetting the school admin must not revoke the
    # platform admin's own token.
    response = client.get(
        "/api/schools",
        headers={
            "Authorization": f"Bearer {platform_admin_token}",
        },
    )

    assert response.status_code == 200

def test_forced_password_change_user_can_access_own_profile(
    client,
    db,
    platform_admin,
):
    platform_admin.must_change_password = True
    db.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    login_data = login_response.json()
    assert login_data["must_change_password"] is True

    token = login_data["access_token"]

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
    assert data["account_type"] == "platform_admin"
    assert data["must_change_password"] is True
