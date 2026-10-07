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
    return {
        "Authorization": (
            f"Bearer {response.json()['access_token']}"
        )
    }


def make_logo(
    size=(200, 200),
    color="blue",
    image_format="PNG",
):
    output = BytesIO()
    Image.new("RGB", size, color).save(
        output,
        format=image_format,
    )
    return output.getvalue()


def test_school_admin_can_upload_and_retrieve_school_logo(
    client,
    school_admin,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "private_upload_dir",
        str(tmp_path),
    )

    headers = login(client, school_admin.email)

    upload_response = client.post(
        "/api/schools/me/logo",
        headers=headers,
        files={
            "logo": (
                "logo.png",
                make_logo(),
                "image/png",
            ),
        },
    )

    assert upload_response.status_code == 200

    body = upload_response.json()

    assert body["logo_url"] == "/api/schools/me/logo"

    logo_files = list(
        (tmp_path / "school_logos").glob("*.jpg")
    )
    assert len(logo_files) == 1

    logo_response = client.get(
        "/api/schools/me/logo",
        headers=headers,
    )

    assert logo_response.status_code == 200
    assert (
        logo_response.headers["content-type"]
        == "image/jpeg"
    )
    assert (
        logo_response.headers["x-content-type-options"]
        == "nosniff"
    )

    with Image.open(
        BytesIO(logo_response.content)
    ) as image:
        assert image.format == "JPEG"
        assert image.size == (200, 200)


def test_school_logo_is_isolated_between_schools(
    client,
    school_admin,
    other_school_admin,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "private_upload_dir",
        str(tmp_path),
    )

    first_headers = login(
        client,
        school_admin.email,
    )
    second_headers = login(
        client,
        other_school_admin.email,
    )

    first_upload = client.post(
        "/api/schools/me/logo",
        headers=first_headers,
        files={
            "logo": (
                "first.png",
                make_logo(color="blue"),
                "image/png",
            ),
        },
    )
    assert first_upload.status_code == 200

    second_before_upload = client.get(
        "/api/schools/me/logo",
        headers=second_headers,
    )
    assert second_before_upload.status_code == 404

    second_upload = client.post(
        "/api/schools/me/logo",
        headers=second_headers,
        files={
            "logo": (
                "second.png",
                make_logo(color="green"),
                "image/png",
            ),
        },
    )
    assert second_upload.status_code == 200

    first_logo = client.get(
        "/api/schools/me/logo",
        headers=first_headers,
    )
    second_logo = client.get(
        "/api/schools/me/logo",
        headers=second_headers,
    )

    assert first_logo.status_code == 200
    assert second_logo.status_code == 200
    assert first_logo.content != second_logo.content


def test_invalid_school_logo_is_rejected(
    client,
    school_admin,
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
        "/api/schools/me/logo",
        headers=headers,
        files={
            "logo": (
                "fake.png",
                b"This is not an image",
                "image/png",
            ),
        },
    )

    assert response.status_code == 400
    assert not list(tmp_path.rglob("*.jpg"))


def test_oversized_school_logo_is_rejected(
    client,
    school_admin,
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
        "/api/schools/me/logo",
        headers=headers,
        files={
            "logo": (
                "large.jpg",
                b"x" * (5 * 1024 * 1024 + 1),
                "image/jpeg",
            ),
        },
    )

    assert response.status_code == 413
    assert not list(tmp_path.rglob("*.jpg"))


def test_uploading_new_school_logo_replaces_old_logo(
    client,
    school_admin,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "private_upload_dir",
        str(tmp_path),
    )

    headers = login(client, school_admin.email)
    logo_url = "/api/schools/me/logo"

    first_response = client.post(
        logo_url,
        headers=headers,
        files={
            "logo": (
                "first.png",
                make_logo(
                    size=(100, 100),
                    color="blue",
                ),
                "image/png",
            ),
        },
    )

    assert first_response.status_code == 200

    logo_directory = tmp_path / "school_logos"

    first_files = list(
        logo_directory.glob("*.jpg")
    )
    assert len(first_files) == 1

    first_file = first_files[0]

    second_response = client.post(
        logo_url,
        headers=headers,
        files={
            "logo": (
                "replacement.png",
                make_logo(
                    size=(300, 150),
                    color="green",
                ),
                "image/png",
            ),
        },
    )

    assert second_response.status_code == 200

    remaining_files = list(
        logo_directory.glob("*.jpg")
    )

    assert len(remaining_files) == 1
    assert remaining_files[0] != first_file
    assert not first_file.exists()

    retrieved = client.get(
        logo_url,
        headers=headers,
    )

    assert retrieved.status_code == 200

    with Image.open(
        BytesIO(retrieved.content)
    ) as image:
        assert image.size == (300, 150)


def test_school_admin_can_delete_school_logo(
    client,
    school_admin,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "private_upload_dir",
        str(tmp_path),
    )

    headers = login(client, school_admin.email)
    logo_url = "/api/schools/me/logo"

    upload_response = client.post(
        logo_url,
        headers=headers,
        files={
            "logo": (
                "logo.png",
                make_logo(),
                "image/png",
            ),
        },
    )

    assert upload_response.status_code == 200

    delete_response = client.delete(
        logo_url,
        headers=headers,
    )

    assert delete_response.status_code == 204

    retrieve_response = client.get(
        logo_url,
        headers=headers,
    )

    assert retrieve_response.status_code == 404

    school_response = client.get(
        "/api/schools/me",
        headers=headers,
    )

    assert school_response.status_code == 200
    assert school_response.json()["logo_url"] is None

    assert not list(
        (tmp_path / "school_logos").glob("*.jpg")
    )


def test_school_logo_requires_authentication(
    client,
):
    logo_url = "/api/schools/me/logo"

    upload_response = client.post(
        logo_url,
        files={
            "logo": (
                "logo.png",
                make_logo(),
                "image/png",
            ),
        },
    )

    assert upload_response.status_code == 401

    retrieve_response = client.get(logo_url)
    assert retrieve_response.status_code == 401

    delete_response = client.delete(logo_url)
    assert delete_response.status_code == 401


def test_school_logo_endpoint_rejects_platform_admin(
    client,
    platform_admin,
):
    headers = login(client, platform_admin.email)

    response = client.get(
        "/api/schools/me/logo",
        headers=headers,
    )

    assert response.status_code == 403
