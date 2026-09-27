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


def create_band(
    client,
    token,
    minimum_average,
    maximum_average,
    teacher_comment,
    principal_comment,
):
    return client.post(
        "/api/performance-comment-bands",
        headers=auth_headers(token),
        json={
            "minimum_average": minimum_average,
            "maximum_average": maximum_average,
            "teacher_comment": teacher_comment,
            "principal_comment": principal_comment,
        },
    )


def test_school_admin_can_create_performance_comment_band(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = create_band(
        client=client,
        token=token,
        minimum_average=80,
        maximum_average=100,
        teacher_comment=(
            "Excellent performance. Keep it up."
        ),
        principal_comment="Excellent",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["school_id"] == school_admin.school_id
    assert data["minimum_average"] == 80
    assert data["maximum_average"] == 100
    assert data["teacher_comment"] == (
        "Excellent performance. Keep it up."
    )
    assert data["principal_comment"] == "Excellent"


def test_performance_comment_bands_are_listed_highest_first(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    low_response = create_band(
        client=client,
        token=token,
        minimum_average=0,
        maximum_average=39.99,
        teacher_comment="Needs improvement.",
        principal_comment="Needs Improvement",
    )

    high_response = create_band(
        client=client,
        token=token,
        minimum_average=80,
        maximum_average=100,
        teacher_comment="Excellent performance.",
        principal_comment="Excellent",
    )

    assert low_response.status_code == 201
    assert high_response.status_code == 201

    response = client.get(
        "/api/performance-comment-bands",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["minimum_average"] == 80
    assert data[1]["minimum_average"] == 0


def test_invalid_performance_comment_band_range_is_rejected(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = create_band(
        client=client,
        token=token,
        minimum_average=80,
        maximum_average=70,
        teacher_comment="Invalid range.",
        principal_comment="Invalid",
    )

    assert response.status_code == 422


def test_performance_comment_band_outside_0_to_100_is_rejected(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    response = create_band(
        client=client,
        token=token,
        minimum_average=-1,
        maximum_average=50,
        teacher_comment="Invalid range.",
        principal_comment="Invalid",
    )

    assert response.status_code == 422


def test_overlapping_performance_comment_band_is_rejected(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    first_response = create_band(
        client=client,
        token=token,
        minimum_average=80,
        maximum_average=100,
        teacher_comment="Excellent performance.",
        principal_comment="Excellent",
    )

    assert first_response.status_code == 201

    response = create_band(
        client=client,
        token=token,
        minimum_average=75,
        maximum_average=85,
        teacher_comment="Very good performance.",
        principal_comment="Very Good",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "This average range overlaps with "
        "an existing performance comment band"
    )


def test_adjacent_non_overlapping_bands_are_allowed(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    first_response = create_band(
        client=client,
        token=token,
        minimum_average=80,
        maximum_average=100,
        teacher_comment="Excellent performance.",
        principal_comment="Excellent",
    )

    second_response = create_band(
        client=client,
        token=token,
        minimum_average=70,
        maximum_average=79.99,
        teacher_comment="Very good performance.",
        principal_comment="Very Good",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201


def test_school_admin_can_update_performance_comment_band(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    create_response = create_band(
        client=client,
        token=token,
        minimum_average=50,
        maximum_average=59.99,
        teacher_comment="Satisfactory performance.",
        principal_comment="Satisfactory",
    )

    assert create_response.status_code == 201

    band_id = create_response.json()["id"]

    response = client.put(
        f"/api/performance-comment-bands/{band_id}",
        headers=auth_headers(token),
        json={
            "teacher_comment": (
                "Satisfactory performance. "
                "There is room for improvement."
            ),
            "principal_comment": "Satisfactory",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["teacher_comment"] == (
        "Satisfactory performance. "
        "There is room for improvement."
    )
    assert data["principal_comment"] == "Satisfactory"


def test_update_cannot_create_overlapping_band(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    first_response = create_band(
        client=client,
        token=token,
        minimum_average=80,
        maximum_average=100,
        teacher_comment="Excellent performance.",
        principal_comment="Excellent",
    )

    second_response = create_band(
        client=client,
        token=token,
        minimum_average=60,
        maximum_average=69.99,
        teacher_comment="Good performance.",
        principal_comment="Good",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    second_id = second_response.json()["id"]

    response = client.put(
        f"/api/performance-comment-bands/{second_id}",
        headers=auth_headers(token),
        json={
            "maximum_average": 85,
        },
    )

    assert response.status_code == 409


def test_school_admin_can_delete_performance_comment_band(
    client,
    school_admin,
):
    token = login(
        client,
        school_admin.email,
    )

    create_response = create_band(
        client=client,
        token=token,
        minimum_average=40,
        maximum_average=49.99,
        teacher_comment="Fair performance.",
        principal_comment="Fair",
    )

    assert create_response.status_code == 201

    band_id = create_response.json()["id"]

    response = client.delete(
        f"/api/performance-comment-bands/{band_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/performance-comment-bands/{band_id}",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 404


def test_performance_comment_bands_are_isolated_by_school(
    client,
    school_admin,
    other_school_admin,
):
    first_token = login(
        client,
        school_admin.email,
    )

    second_token = login(
        client,
        other_school_admin.email,
    )

    first_response = create_band(
        client=client,
        token=first_token,
        minimum_average=80,
        maximum_average=100,
        teacher_comment="School one excellent.",
        principal_comment="Excellent",
    )

    second_response = create_band(
        client=client,
        token=second_token,
        minimum_average=80,
        maximum_average=100,
        teacher_comment="School two excellent.",
        principal_comment="Outstanding",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        "/api/performance-comment-bands",
        headers=auth_headers(first_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["school_id"] == school_admin.school_id
    assert data[0]["teacher_comment"] == (
        "School one excellent."
    )


def test_cross_school_performance_comment_band_is_hidden(
    client,
    school_admin,
    other_school_admin,
):
    first_token = login(
        client,
        school_admin.email,
    )

    second_token = login(
        client,
        other_school_admin.email,
    )

    create_response = create_band(
        client=client,
        token=second_token,
        minimum_average=80,
        maximum_average=100,
        teacher_comment="Other school comment.",
        principal_comment="Excellent",
    )

    assert create_response.status_code == 201

    band_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/performance-comment-bands/{band_id}",
        headers=auth_headers(first_token),
    )

    assert get_response.status_code == 404

    update_response = client.put(
        f"/api/performance-comment-bands/{band_id}",
        headers=auth_headers(first_token),
        json={
            "principal_comment": "Compromised",
        },
    )

    assert update_response.status_code == 404

    delete_response = client.delete(
        f"/api/performance-comment-bands/{band_id}",
        headers=auth_headers(first_token),
    )

    assert delete_response.status_code == 404


def test_platform_admin_cannot_create_performance_comment_band(
    client,
    platform_admin,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = create_band(
        client=client,
        token=token,
        minimum_average=80,
        maximum_average=100,
        teacher_comment="Excellent performance.",
        principal_comment="Excellent",
    )

    assert response.status_code == 403


def test_performance_comment_bands_require_authentication(
    client,
):
    response = client.get(
        "/api/performance-comment-bands"
    )

    assert response.status_code == 401
