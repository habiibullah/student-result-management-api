def login(client, email):
    return client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_inactive_school_admin_cannot_login(
    client,
    db,
    school_one,
    school_admin,
):
    school_one.is_active = False
    db.commit()

    response = login(client, school_admin.email)

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "School account is inactive"
    )


def test_existing_token_blocked_after_school_deactivation(
    client,
    db,
    school_one,
    school_admin,
):
    login_response = login(client, school_admin.email)

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    school_one.is_active = False
    db.commit()

    response = client.get(
        "/api/users/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "School account is inactive"
    )


def test_platform_admin_can_reactivate_school(
    client,
    db,
    school_one,
    school_admin,
    platform_admin,
):
    school_one.is_active = False
    db.commit()

    platform_login = login(
        client,
        platform_admin.email,
    )

    assert platform_login.status_code == 200

    token = platform_login.json()["access_token"]

    response = client.patch(
        f"/api/schools/{school_one.id}/status",
        json={"is_active": True},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True

    school_login = login(client, school_admin.email)

    assert school_login.status_code == 200

from app.models import User


def test_inactive_school_teacher_cannot_login(
    client,
    db,
    school_one,
    school_one_teacher,
):
    teacher_user = db.get(
        User,
        school_one_teacher.user_id,
    )

    school_one.is_active = False
    db.commit()

    response = login(
        client,
        teacher_user.email,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "School account is inactive"
    )


def test_existing_teacher_token_blocked_after_deactivation(
    client,
    db,
    school_one,
    school_one_teacher,
):
    teacher_user = db.get(
        User,
        school_one_teacher.user_id,
    )

    login_response = login(
        client,
        teacher_user.email,
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    school_one.is_active = False
    db.commit()

    response = client.get(
        "/api/users/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "School account is inactive"
    )