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


def test_class_list_contains_only_current_school(
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


def test_class_cross_school_read_is_hidden(
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


def test_class_cross_school_update_is_blocked(
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


def test_subject_list_contains_only_current_school(
    client,
    school_admin,
    school_one_subject,
    school_two_subject,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/subjects",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        item["id"]
        for item in data
    }

    assert school_one_subject.id in returned_ids
    assert school_two_subject.id not in returned_ids


def test_subject_cross_school_read_is_hidden(
    client,
    school_admin,
    school_two_subject,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/subjects/{school_two_subject.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Subject not found"


def test_subject_cross_school_update_is_blocked(
    client,
    school_admin,
    school_two_subject,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.put(
        f"/api/subjects/{school_two_subject.id}",
        headers=auth_headers(token),
        json={
            "name": "Compromised Subject",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Subject not found"


def test_teacher_list_contains_only_current_school(
    client,
    school_admin,
    school_one_teacher,
    school_two_teacher,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/teachers",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        item["id"]
        for item in data
    }

    assert school_one_teacher.id in returned_ids
    assert school_two_teacher.id not in returned_ids


def test_teacher_cross_school_read_is_hidden(
    client,
    school_admin,
    school_two_teacher,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/teachers/{school_two_teacher.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Teacher not found"


def test_teacher_cross_school_update_is_blocked(
    client,
    school_admin,
    school_two_teacher,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.put(
        f"/api/teachers/{school_two_teacher.id}",
        headers=auth_headers(token),
        json={
            "first_name": "Compromised",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Teacher not found"


def test_student_list_contains_only_current_school(
    client,
    school_admin,
    school_one_student,
    school_two_student,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/students",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        item["id"]
        for item in data
    }

    assert school_one_student.id in returned_ids
    assert school_two_student.id not in returned_ids


def test_student_cross_school_read_is_hidden(
    client,
    school_admin,
    school_two_student,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/students/{school_two_student.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_student_cross_school_update_is_blocked(
    client,
    school_admin,
    school_two_student,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/students/{school_two_student.id}",
        headers=auth_headers(token),
        json={
            "first_name": "Compromised",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"


def test_school_admin_can_read_own_class(
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
    assert response.json()["id"] == school_one_class.id


def test_school_admin_can_read_own_subject(
    client,
    school_admin,
    school_one_subject,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/subjects/{school_one_subject.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == school_one_subject.id


def test_school_admin_can_read_own_teacher(
    client,
    school_admin,
    school_one_teacher,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/teachers/{school_one_teacher.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == school_one_teacher.id


def test_school_admin_can_read_own_student(
    client,
    school_admin,
    school_one_student,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/students/{school_one_student.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == school_one_student.id
