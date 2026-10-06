from app.models import Enrollment, Student
from app.models.result_publication import ResultPublication


PASSWORD = "TestPassword123!"


def _login(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _register(
    client,
    token,
    class_id,
    academic_session_id,
    students,
):
    return client.post(
        "/api/students/bulk-register",
        headers=_auth(token),
        json={
            "class_id": class_id,
            "academic_session_id": academic_session_id,
            "students": students,
        },
    )


def test_school_admin_can_register_one_student_and_enroll_automatically(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": "ADMIN/ONE001",
                "first_name": "Amina",
                "last_name": "Yusuf",
                "gender": "Female",
            }
        ],
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 1
    assert data["created"] == 1
    assert data["rejected"] == 0
    assert len(data["successes"]) == 1
    assert data["errors"] == []

    success = data["successes"][0]

    assert success["row"] == 1
    assert success["student"]["admission_number"] == "ADMIN/ONE001"

    student = (
        db.query(Student)
        .filter(
            Student.school_id == school_admin.school_id,
            Student.admission_number == "ADMIN/ONE001",
        )
        .one()
    )

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student.id,
            Enrollment.class_id == school_one_class.id,
            Enrollment.academic_session_id == academic_session_one.id,
        )
        .one()
    )

    assert success["enrollment_id"] == enrollment.id


def test_school_admin_can_bulk_register_students(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": "ADMIN/BULK001",
                "first_name": "Fatimah",
                "last_name": "Ibrahim",
                "gender": "Female",
            },
            {
                "admission_number": "ADMIN/BULK002",
                "first_name": "Yusuf",
                "last_name": "Abdullah",
                "gender": "Male",
            },
            {
                "admission_number": "ADMIN/BULK003",
                "first_name": "Maryam",
                "last_name": "Ali",
            },
        ],
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 3
    assert data["created"] == 3
    assert data["rejected"] == 0
    assert data["errors"] == []

    assert [
        item["row"] for item in data["successes"]
    ] == [1, 2, 3]

    admission_numbers = {
        item["student"]["admission_number"]
        for item in data["successes"]
    }

    assert admission_numbers == {
        "ADMIN/BULK001",
        "ADMIN/BULK002",
        "ADMIN/BULK003",
    }

    students = (
        db.query(Student)
        .filter(
            Student.school_id == school_admin.school_id,
            Student.admission_number.in_(admission_numbers),
        )
        .all()
    )

    assert len(students) == 3

    student_ids = [student.id for student in students]

    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id.in_(student_ids),
            Enrollment.class_id == school_one_class.id,
            Enrollment.academic_session_id == academic_session_one.id,
        )
        .all()
    )

    assert len(enrollments) == 3


def test_bulk_registration_rejects_existing_student_and_continues(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": school_one_student.admission_number,
                "first_name": "Duplicate",
                "last_name": "Student",
            },
            {
                "admission_number": "ADMIN/VALID001",
                "first_name": "Valid",
                "last_name": "Student",
            },
        ],
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 2
    assert data["created"] == 1
    assert data["rejected"] == 1

    assert data["successes"][0]["row"] == 2
    assert (
        data["successes"][0]["student"]["admission_number"]
        == "ADMIN/VALID001"
    )

    assert data["errors"][0]["row"] == 1
    assert (
        data["errors"][0]["admission_number"]
        == school_one_student.admission_number
    )

    student = (
        db.query(Student)
        .filter(
            Student.school_id == school_admin.school_id,
            Student.admission_number == "ADMIN/VALID001",
        )
        .one()
    )

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == student.id,
            Enrollment.class_id == school_one_class.id,
            Enrollment.academic_session_id == academic_session_one.id,
        )
        .one()
    )

    assert enrollment is not None


def test_bulk_registration_rejects_duplicate_within_same_request(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": "ADMIN/SAME001",
                "first_name": "First",
                "last_name": "Student",
            },
            {
                "admission_number": "ADMIN/SAME001",
                "first_name": "Second",
                "last_name": "Student",
            },
        ],
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 2
    assert data["created"] == 1
    assert data["rejected"] == 1

    assert data["successes"][0]["row"] == 1
    assert data["errors"][0]["row"] == 2

    count = (
        db.query(Student)
        .filter(
            Student.school_id == school_admin.school_id,
            Student.admission_number == "ADMIN/SAME001",
        )
        .count()
    )

    assert count == 1


def test_bulk_registration_can_reject_multiple_duplicates_and_continue(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": school_one_student.admission_number,
                "first_name": "Duplicate",
                "last_name": "Existing",
            },
            {
                "admission_number": "ADMIN/MULTI001",
                "first_name": "Valid",
                "last_name": "One",
            },
            {
                "admission_number": "ADMIN/MULTI001",
                "first_name": "Duplicate",
                "last_name": "Request",
            },
            {
                "admission_number": "ADMIN/MULTI002",
                "first_name": "Valid",
                "last_name": "Two",
            },
        ],
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 4
    assert data["created"] == 2
    assert data["rejected"] == 2

    assert [
        success["row"] for success in data["successes"]
    ] == [2, 4]

    assert [
        error["row"] for error in data["errors"]
    ] == [1, 3]


def test_school_admin_cannot_register_into_class_from_another_school(
    client,
    school_admin,
    school_two_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_two_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": "ADMIN/CROSSCLASS001",
                "first_name": "Cross",
                "last_name": "Class",
            }
        ],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found"


def test_school_admin_cannot_register_into_session_from_another_school(
    client,
    school_admin,
    school_one_class,
    academic_session_two,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_two.id,
        [
            {
                "admission_number": "ADMIN/CROSSSESSION001",
                "first_name": "Cross",
                "last_name": "Session",
            }
        ],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Academic session not found"


def test_teacher_cannot_use_school_admin_bulk_registration_endpoint(
    client,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_one_teacher.user.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": "ADMIN/TEACHER001",
                "first_name": "Teacher",
                "last_name": "Blocked",
            }
        ],
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_bulk_register_students(
    client,
    school_one_class,
    academic_session_one,
):
    response = client.post(
        "/api/students/bulk-register",
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "ADMIN/NOAUTH001",
                    "first_name": "No",
                    "last_name": "Auth",
                }
            ],
        },
    )

    assert response.status_code == 401


def test_bulk_registration_requires_at_least_one_student(
    client,
    school_admin,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [],
    )

    assert response.status_code == 422


def test_bulk_registration_rejects_more_than_200_students(
    client,
    school_admin,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    students = [
        {
            "admission_number": f"ADMIN/MAX{i:03d}",
            "first_name": "Bulk",
            "last_name": "Student",
        }
        for i in range(201)
    ]

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        students,
    )

    assert response.status_code == 422


def test_bulk_registration_validates_required_student_fields(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": "A",
                "first_name": "B",
                "last_name": "C",
            }
        ],
    )

    assert response.status_code == 422

    count = (
        db.query(Student)
        .filter(
            Student.school_id == school_admin.school_id,
            Student.admission_number == "A",
        )
        .count()
    )

    assert count == 0


def test_bulk_registration_preserves_optional_student_fields(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": "ADMIN/OPTIONAL001",
                "first_name": "Hafsat",
                "last_name": "Abubakar",
                "gender": "Female",
                "date_of_birth": "2013-05-12",
            }
        ],
    )

    assert response.status_code == 201, response.text

    student = (
        db.query(Student)
        .filter(
            Student.school_id == school_admin.school_id,
            Student.admission_number == "ADMIN/OPTIONAL001",
        )
        .one()
    )

    assert student.gender == "Female"
    assert student.date_of_birth.isoformat() == "2013-05-12"


def test_published_results_block_school_admin_bulk_registration(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
    first_term,
):
    publication = ResultPublication(
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    db.add(publication)
    db.commit()

    token = _login(client, school_admin.email)

    response = _register(
        client,
        token,
        school_one_class.id,
        academic_session_one.id,
        [
            {
                "admission_number": "ADMIN/LOCKED001",
                "first_name": "Locked",
                "last_name": "Student",
            }
        ],
    )

    assert response.status_code == 409

    count = (
        db.query(Student)
        .filter(
            Student.school_id == school_admin.school_id,
            Student.admission_number == "ADMIN/LOCKED001",
        )
        .count()
    )

    assert count == 0