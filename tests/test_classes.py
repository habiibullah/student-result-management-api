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


def test_school_admin_can_create_class(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/classes",
        headers=auth_headers(token),
        json={
            "name": "Senior Secondary One",
            "code": "SS1",
            "description": "Senior secondary class",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Senior Secondary One"
    assert data["code"] == "SS1"
    assert data["description"] == "Senior secondary class"
    assert data["school_id"] == school_admin.school_id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_duplicate_class_code_in_same_school_is_rejected(
    client,
    school_admin,
    school_one_class,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/classes",
        headers=auth_headers(token),
        json={
            "name": "Another Junior Secondary One",
            "code": school_one_class.code,
            "description": "Duplicate code",
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Class with this code already exists in this school"
    )


def test_same_class_code_is_allowed_in_different_schools(
    client,
    other_school_admin,
    school_one_class,
):
    token = login(
        client,
        other_school_admin.email,
    )

    response = client.post(
        "/api/classes",
        headers=auth_headers(token),
        json={
            "name": "Junior Secondary One",
            "code": school_one_class.code,
            "description": "Class belonging to school two",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["code"] == school_one_class.code
    assert data["school_id"] == other_school_admin.school_id


def test_unauthenticated_user_cannot_create_class(
    client,
):
    response = client.post(
        "/api/classes",
        json={
            "name": "Senior Secondary One",
            "code": "SS1",
        },
    )

    assert response.status_code == 401

def test_school_user_can_list_own_classes(
    client,
    school_admin,
    school_one_class,
    school_two_class,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/classes",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        item["id"]
        for item in data
    }

    assert school_one_class.id in returned_ids
    assert school_two_class.id not in returned_ids


def test_school_admin_can_get_class_by_id(
    client,
    school_admin,
    school_one_class,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/classes/{school_one_class.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == school_one_class.id
    assert data["school_id"] == school_admin.school_id
    assert data["name"] == school_one_class.name
    assert data["code"] == school_one_class.code
    assert data["description"] == school_one_class.description


def test_cross_school_class_is_not_visible_by_id(
    client,
    school_admin,
    school_two_class,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/classes/{school_two_class.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found"


def test_unknown_class_returns_404(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/classes/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found"


def test_unauthenticated_user_cannot_list_classes(
    client,
):
    response = client.get(
        "/api/classes",
    )

    assert response.status_code == 401


def test_unauthenticated_user_cannot_get_class(
    client,
    school_one_class,
):
    response = client.get(
        f"/api/classes/{school_one_class.id}",
    )

    assert response.status_code == 401

def test_school_admin_can_update_class(
    client,
    school_admin,
    school_one_class,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.put(
        f"/api/classes/{school_one_class.id}",
        headers=auth_headers(token),
        json={
            "name": "Updated Junior Secondary One",
            "code": "JSS1A",
            "description": "Updated class description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Junior Secondary One"
    assert data["code"] == "JSS1A"
    assert data["description"] == "Updated class description"


def test_school_admin_can_partially_update_class(
    client,
    school_admin,
    school_one_class,
):
    original_code = school_one_class.code
    original_description = school_one_class.description

    token = login(
        client,
        school_admin.email,
    )

    response = client.put(
        f"/api/classes/{school_one_class.id}",
        headers=auth_headers(token),
        json={
            "name": "Renamed Class",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Renamed Class"
    assert data["code"] == original_code
    assert data["description"] == original_description


def test_duplicate_class_code_on_update_is_rejected(
    client,
    db,
    school_admin,
    school_one,
    school_one_class,
):
    from app.models import Class

    second_class = Class(
        school_id=school_one.id,
        name="Junior Secondary Two",
        code="JSS2",
        description="Second test class",
    )

    db.add(second_class)
    db.commit()
    db.refresh(second_class)

    token = login(
        client,
        school_admin.email,
    )

    response = client.put(
        f"/api/classes/{second_class.id}",
        headers=auth_headers(token),
        json={
            "code": school_one_class.code,
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Class with this code already exists in this school"
    )


def test_school_admin_can_clear_class_description(
    client,
    school_admin,
    school_one_class,
):
    assert school_one_class.description is not None

    token = login(
        client,
        school_admin.email,
    )

    response = client.put(
        f"/api/classes/{school_one_class.id}",
        headers=auth_headers(token),
        json={
            "description": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_cross_school_class_update_is_blocked(
    client,
    school_admin,
    school_two_class,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.put(
        f"/api/classes/{school_two_class.id}",
        headers=auth_headers(token),
        json={
            "name": "Compromised Class",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found"


def test_unauthenticated_user_cannot_update_class(
    client,
    school_one_class,
):
    response = client.put(
        f"/api/classes/{school_one_class.id}",
        json={
            "name": "Unauthorized Update",
        },
    )

    assert response.status_code == 401

def test_school_admin_can_delete_unused_class(
    client,
    db,
    school_admin,
    school_one,
):
    from app.models import Class

    unused_class = Class(
        school_id=school_one.id,
        name="Senior Secondary Three",
        code="SS3",
        description="Unused test class",
    )

    db.add(unused_class)
    db.commit()
    db.refresh(unused_class)

    class_id = unused_class.id

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/classes/{class_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    db.expire_all()

    deleted_class = db.get(Class, class_id)
    assert deleted_class is None


def test_class_with_assessment_cannot_be_deleted(
    client,
    school_admin,
    school_one_class,
    active_term_assessment,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/classes/{school_one_class.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Class cannot be deleted because it already has "
        "academic records or related assignments."
    )


def test_cross_school_class_delete_is_blocked(
    client,
    school_admin,
    school_two_class,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/classes/{school_two_class.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found"


def test_unknown_class_delete_returns_404(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        "/api/classes/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found"


def test_unauthenticated_user_cannot_delete_class(
    client,
    school_one_class,
):
    response = client.delete(
        f"/api/classes/{school_one_class.id}",
    )

    assert response.status_code == 401
