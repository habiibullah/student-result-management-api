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


def test_platform_admin_can_create_platform_admin(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.post(
        "/api/admin-management/platform-admins",
        headers=auth_headers(token),
        json={
            "email": "new.platform.admin@example.com",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == (
        "new.platform.admin@example.com"
    )
    assert data["role"] == "admin"
    assert data["account_type"] == "platform_admin"
    assert data["school_id"] is None
    assert data["is_active"] is True


def test_school_admin_cannot_create_platform_admin(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/admin-management/platform-admins",
        headers=auth_headers(token),
        json={
            "email": (
                "forbidden.platform.admin@example.com"
            ),
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 403


def test_platform_admin_can_create_school_admin(
    client,
    platform_admin,
    school_one,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.post(
        "/api/admin-management/school-admins",
        headers=auth_headers(token),
        json={
            "email": (
                "created.school.admin@example.com"
            ),
            "password": "TestPassword123!",
            "school_id": school_one.id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == (
        "created.school.admin@example.com"
    )
    assert data["role"] == "admin"
    assert data["account_type"] == "school_admin"
    assert data["school_id"] == school_one.id
    assert data["is_active"] is True


def test_school_admin_can_create_admin_for_own_school(
    client,
    school_admin,
    school_one,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/admin-management/school-admins",
        headers=auth_headers(token),
        json={
            "email": (
                "new.own.school.admin@example.com"
            ),
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["school_id"] == school_one.id
    assert data["account_type"] == "school_admin"
    assert data["is_active"] is True


def test_school_admin_cannot_create_admin_for_other_school(
    client,
    school_admin,
    school_two,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/admin-management/school-admins",
        headers=auth_headers(token),
        json={
            "email": (
                "forbidden.school.admin@example.com"
            ),
            "password": "TestPassword123!",
            "school_id": school_two.id,
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "You cannot create an administrator "
        "for another school"
    )


def test_platform_admin_can_list_platform_admins(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.get(
        "/api/admin-management/platform-admins",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    assert data[0]["id"] == platform_admin.id
    assert data[0]["email"] == platform_admin.email
    assert data[0]["account_type"] == (
        "platform_admin"
    )
    assert data[0]["school_id"] is None


def test_school_admin_cannot_list_platform_admins(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/admin-management/platform-admins",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_platform_admin_can_list_all_school_admins(
    client,
    platform_admin,
    school_admin,
    other_school_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.get(
        "/api/admin-management/school-admins",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        admin["id"]
        for admin in data
    }

    assert school_admin.id in returned_ids
    assert other_school_admin.id in returned_ids


def test_platform_admin_can_filter_school_admins(
    client,
    platform_admin,
    school_admin,
    other_school_admin,
    school_one,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.get(
        (
            "/api/admin-management/"
            f"school-admins?school_id={school_one.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        admin["id"]
        for admin in data
    }

    assert school_admin.id in returned_ids
    assert other_school_admin.id not in returned_ids

    for admin in data:
        assert admin["school_id"] == school_one.id


def test_school_admin_can_list_only_own_school_admins(
    client,
    school_admin,
    second_school_admin,
    other_school_admin,
    school_one,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/admin-management/school-admins",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        admin["id"]
        for admin in data
    }

    assert school_admin.id in returned_ids
    assert second_school_admin.id in returned_ids
    assert other_school_admin.id not in returned_ids

    for admin in data:
        assert admin["school_id"] == school_one.id


def test_school_admin_cannot_view_other_school_admins(
    client,
    school_admin,
    school_two,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        (
            "/api/admin-management/"
            f"school-admins?school_id={school_two.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "You cannot view administrators "
        "from another school"
    )


def test_platform_admin_cannot_deactivate_self(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        (
            "/api/admin-management/"
            f"platform-admins/{platform_admin.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "You cannot deactivate your own "
        "platform administrator account"
    )


def test_platform_admin_can_deactivate_and_reactivate_another_platform_admin(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    create_response = client.post(
        "/api/admin-management/platform-admins",
        headers=auth_headers(token),
        json={
            "email": (
                "second.platform.admin@example.com"
            ),
            "password": "TestPassword123!",
        },
    )

    assert create_response.status_code == 201

    second_admin = create_response.json()

    deactivate_response = client.patch(
        (
            "/api/admin-management/platform-admins/"
            f"{second_admin['id']}/status"
        ),
        headers=auth_headers(token),
        json={
            "is_active": False,
        },
    )

    assert deactivate_response.status_code == 200

    deactivated = deactivate_response.json()

    assert deactivated["is_active"] is False

    reactivate_response = client.patch(
        (
            "/api/admin-management/platform-admins/"
            f"{second_admin['id']}/status"
        ),
        headers=auth_headers(token),
        json={
            "is_active": True,
        },
    )

    assert reactivate_response.status_code == 200

    reactivated = reactivate_response.json()

    assert reactivated["is_active"] is True


def test_school_admin_cannot_deactivate_self(
    client,
    school_admin,
    second_school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            "/api/admin-management/"
            f"school-admins/{school_admin.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "You cannot deactivate your own "
        "school administrator account"
    )


def test_school_admin_can_deactivate_and_reactivate_another_admin(
    client,
    school_admin,
    second_school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    deactivate_response = client.patch(
        (
            "/api/admin-management/school-admins/"
            f"{second_school_admin.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "is_active": False,
        },
    )

    assert deactivate_response.status_code == 200

    assert (
        deactivate_response.json()["is_active"]
        is False
    )

    reactivate_response = client.patch(
        (
            "/api/admin-management/school-admins/"
            f"{second_school_admin.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "is_active": True,
        },
    )

    assert reactivate_response.status_code == 200

    assert (
        reactivate_response.json()["is_active"]
        is True
    )


def test_school_admin_cannot_manage_other_school_admin(
    client,
    school_admin,
    other_school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            "/api/admin-management/school-admins/"
            f"{other_school_admin.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 403

    assert response.json()["detail"] == (
        "You cannot manage an administrator "
        "from another school"
    )


def test_last_active_school_admin_cannot_be_deactivated(
    client,
    platform_admin,
    school_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        (
            "/api/admin-management/"
            f"school-admins/{school_admin.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "The last active administrator "
        "for this school cannot be deactivated"
    )


def test_platform_admin_missing_school_id_when_creating_school_admin(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.post(
        "/api/admin-management/school-admins",
        headers=auth_headers(token),
        json={
            "email": (
                "missing.school.admin@example.com"
            ),
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "school_id is required when a platform "
        "admin creates a school admin"
    )


def test_duplicate_admin_email_is_rejected(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.post(
        "/api/admin-management/platform-admins",
        headers=auth_headers(token),
        json={
            "email": platform_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "A user with this email already exists"
    )
