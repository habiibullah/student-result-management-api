from io import BytesIO

from PIL import Image

from app.core.config import settings


def login(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def make_photo():
    output = BytesIO()
    Image.new("RGB", (100, 100), "blue").save(
        output,
        format="JPEG",
    )
    return output.getvalue()


def test_school_admin_can_upload_and_retrieve_student_photo(
    client,
    school_admin,
    school_one_student,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "private_upload_dir",
        str(tmp_path),
    )

    headers = login(client, school_admin.email)
    student_id = school_one_student.id

    upload_response = client.post(
        f"/api/students/{student_id}/photo",
        headers=headers,
        files={
            "photo": (
                "student.jpg",
                make_photo(),
                "image/jpeg",
            ),
        },
    )

    assert upload_response.status_code == 200
    assert upload_response.json()["has_profile_photo"] is True
    assert "profile_photo_path" not in upload_response.json()

    photo_response = client.get(
        f"/api/students/{student_id}/photo",
        headers=headers,
    )

    assert photo_response.status_code == 200
    assert photo_response.headers["content-type"] == "image/jpeg"

    with Image.open(BytesIO(photo_response.content)) as image:
        assert image.format == "JPEG"
        assert image.size == (100, 100)


def test_other_school_cannot_access_student_photo(
    client,
    school_admin,
    other_school_admin,
    school_one_student,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "private_upload_dir",
        str(tmp_path),
    )

    student_id = school_one_student.id
    owner_headers = login(client, school_admin.email)
    other_headers = login(client, other_school_admin.email)

    upload_response = client.post(
        f"/api/students/{student_id}/photo",
        headers=owner_headers,
        files={
            "photo": (
                "student.jpg",
                make_photo(),
                "image/jpeg",
            ),
        },
    )

    assert upload_response.status_code == 200

    other_school_upload = client.post(
        f"/api/students/{student_id}/photo",
        headers=other_headers,
        files={
            "photo": (
                "student.jpg",
                make_photo(),
                "image/jpeg",
            ),
        },
    )

    assert other_school_upload.status_code == 404

    other_school_get = client.get(
        f"/api/students/{student_id}/photo",
        headers=other_headers,
    )

    assert other_school_get.status_code == 404


def test_invalid_photo_is_rejected(
    client,
    school_admin,
    school_one_student,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "private_upload_dir",
        str(tmp_path),
    )

    headers = login(client, school_admin.email)

    response = client.post(
        f"/api/students/{school_one_student.id}/photo",
        headers=headers,
        files={
            "photo": (
                "invalid.jpg",
                b"This is not an image",
                "image/jpeg",
            ),
        },
    )

    assert response.status_code == 400


def test_uploading_new_photo_replaces_old_photo(
    client,
    school_admin,
    school_one_student,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "private_upload_dir",
        str(tmp_path),
    )

    headers = login(client, school_admin.email)
    student_id = school_one_student.id
    photo_url = f"/api/students/{student_id}/photo"

    first_response = client.post(
        photo_url,
        headers=headers,
        files={
            "photo": (
                "first.jpg",
                make_photo(),
                "image/jpeg",
            ),
        },
    )
    assert first_response.status_code == 200

    photo_directory = tmp_path / "student_photos"
    first_files = list(photo_directory.glob("*.jpg"))
    assert len(first_files) == 1
    first_file = first_files[0]

    replacement = BytesIO()
    Image.new("RGB", (200, 150), "green").save(
        replacement,
        format="JPEG",
    )

    second_response = client.post(
        photo_url,
        headers=headers,
        files={
            "photo": (
                "replacement.jpg",
                replacement.getvalue(),
                "image/jpeg",
            ),
        },
    )
    assert second_response.status_code == 200
    assert second_response.json()["has_profile_photo"] is True

    remaining_files = list(photo_directory.glob("*.jpg"))
    assert len(remaining_files) == 1
    assert remaining_files[0] != first_file
    assert not first_file.exists()

    retrieved_response = client.get(
        photo_url,
        headers=headers,
    )
    assert retrieved_response.status_code == 200

    with Image.open(BytesIO(retrieved_response.content)) as image:
        assert image.size == (200, 150)

def test_oversized_photo_is_rejected(
    client,
    school_admin,
    school_one_student,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "private_upload_dir",
        str(tmp_path),
    )

    headers = login(client, school_admin.email)
    student_id = school_one_student.id

    response = client.post(
        f"/api/students/{student_id}/photo",
        headers=headers,
        files={
            "photo": (
                "large.jpg",
                b"x" * (5 * 1024 * 1024 + 1),
                "image/jpeg",
            ),
        },
    )

    assert response.status_code == 413
    assert not list(tmp_path.rglob("*.jpg"))


def test_student_photo_requires_authentication(
    client,
    school_one_student,
):
    student_id = school_one_student.id
    photo_url = f"/api/students/{student_id}/photo"

    upload_response = client.post(
        photo_url,
        files={
            "photo": (
                "student.jpg",
                make_photo(),
                "image/jpeg",
            ),
        },
    )

    assert upload_response.status_code == 401

    retrieve_response = client.get(photo_url)

    assert retrieve_response.status_code == 401
