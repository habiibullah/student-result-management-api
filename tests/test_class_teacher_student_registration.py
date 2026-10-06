from app.models import ClassTeacherAssignment, Enrollment, Student


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


def _assign_class_teacher(
    db,
    teacher,
    class_,
    academic_session,
):
    assignment = ClassTeacherAssignment(
        teacher_id=teacher.id,
        class_id=class_.id,
        academic_session_id=academic_session.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def test_class_teacher_can_register_student_into_assigned_class(
    client,
    db,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "SCH1/NEW001",
                    "first_name": "Amina",
                    "last_name": "Yusuf",
                    "gender": "Female",
                }
            ],
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 1
    assert data["created"] == 1
    assert data["rejected"] == 0
    assert len(data["successes"]) == 1
    assert data["errors"] == []

    created_student = data["successes"][0]["student"]

    assert created_student["admission_number"] == "SCH1/NEW001"
    assert created_student["first_name"] == "Amina"
    assert created_student["last_name"] == "Yusuf"
    assert data["successes"][0]["row"] == 1

    student = db.query(Student).filter(
        Student.admission_number == "SCH1/NEW001",
        Student.school_id == school_one_teacher.school_id,
    ).one()

    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student.id,
        Enrollment.class_id == school_one_class.id,
        Enrollment.academic_session_id == academic_session_one.id,
    ).one()

    assert data["successes"][0]["enrollment_id"] == enrollment.id

def test_class_teacher_can_bulk_register_students(
    client,
    db,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "SCH1/BULK001",
                    "first_name": "Fatimah",
                    "last_name": "Ibrahim",
                    "gender": "Female",
                },
                {
                    "admission_number": "SCH1/BULK002",
                    "first_name": "Yusuf",
                    "last_name": "Abdullah",
                    "gender": "Male",
                },
                {
                    "admission_number": "SCH1/BULK003",
                    "first_name": "Maryam",
                    "last_name": "Ali",
                },
            ],
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 3
    assert data["created"] == 3
    assert data["rejected"] == 0
    assert len(data["successes"]) == 3
    assert data["errors"] == []

    assert [
        item["student"]["admission_number"]
        for item in data["successes"]
    ] == [
        "SCH1/BULK001",
        "SCH1/BULK002",
        "SCH1/BULK003",
    ]

    assert [
        item["row"]
        for item in data["successes"]
    ] == [1, 2, 3]

    students = (
        db.query(Student)
        .filter(
            Student.school_id == school_one_teacher.school_id,
            Student.admission_number.in_(
                [
                    "SCH1/BULK001",
                    "SCH1/BULK002",
                    "SCH1/BULK003",
                ]
            ),
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
            Enrollment.academic_session_id
            == academic_session_one.id,
        )
        .all()
    )

    assert len(enrollments) == 3

def test_bulk_registration_rejects_duplicate_and_creates_valid_students(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": school_one_student.admission_number,
                    "first_name": "Duplicate",
                    "last_name": "Student",
                },
                {
                    "admission_number": "SCH1/VALID001",
                    "first_name": "Hassan",
                    "last_name": "Ibrahim",
                },
            ],
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 2
    assert data["created"] == 1
    assert data["rejected"] == 1

    assert len(data["successes"]) == 1
    assert data["successes"][0]["row"] == 2
    assert (
        data["successes"][0]["student"]["admission_number"]
        == "SCH1/VALID001"
    )

    assert len(data["errors"]) == 1
    assert data["errors"][0]["row"] == 1
    assert (
        data["errors"][0]["admission_number"]
        == school_one_student.admission_number
    )
    assert data["errors"][0]["detail"] == (
        "A student with this admission number "
        "already exists in this school"
    )

    created_student = db.query(Student).filter(
        Student.admission_number == "SCH1/VALID001",
        Student.school_id == school_one_teacher.school_id,
    ).one()

    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == created_student.id,
        Enrollment.class_id == school_one_class.id,
        Enrollment.academic_session_id == academic_session_one.id,
    ).one()

    assert enrollment.student_id == created_student.id

def test_unassigned_teacher_cannot_register_students(
    client,
    db,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "SCH1/UNAUTH001",
                    "first_name": "Unauthorized",
                    "last_name": "Student",
                }
            ],
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Class teacher access required"
    )

    student = db.query(Student).filter(
        Student.admission_number == "SCH1/UNAUTH001",
    ).first()

    assert student is None


def test_class_teacher_cannot_register_into_different_class(
    client,
    db,
    school_one_teacher,
    school_one_class,
    school_two_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_two_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "SCH1/WRONGCLASS001",
                    "first_name": "Wrong",
                    "last_name": "Class",
                }
            ],
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Class teacher access required"
    )

    student = db.query(Student).filter(
        Student.admission_number == "SCH1/WRONGCLASS001",
    ).first()

    assert student is None


def test_class_teacher_cannot_register_into_unassigned_session(
    client,
    db,
    school_one,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    from app.models.academic_session import AcademicSession

    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    other_session = AcademicSession(
        school_id=school_one.id,
        name="2098/2099",
        is_current=False,
    )
    db.add(other_session)
    db.commit()
    db.refresh(other_session)

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": other_session.id,
            "students": [
                {
                    "admission_number": "SCH1/WRONGSESSION001",
                    "first_name": "Wrong",
                    "last_name": "Session",
                }
            ],
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Class teacher access required"
    )

    student = db.query(Student).filter(
        Student.admission_number == "SCH1/WRONGSESSION001",
    ).first()

    assert student is None


def test_school_admin_cannot_use_class_teacher_registration_endpoint(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
):
    token = _login(client, school_admin.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "SCH1/ADMINCT001",
                    "first_name": "Admin",
                    "last_name": "Attempt",
                }
            ],
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Class teacher access required"
    )

    student = db.query(Student).filter(
        Student.admission_number == "SCH1/ADMINCT001",
    ).first()

    assert student is None


def test_unauthenticated_user_cannot_register_students(
    client,
    db,
    school_one_class,
    academic_session_one,
):
    response = client.post(
        "/api/students/class-teacher/register",
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "SCH1/NOAUTH001",
                    "first_name": "No",
                    "last_name": "Authentication",
                }
            ],
        },
    )

    assert response.status_code == 401

    student = db.query(Student).filter(
        Student.admission_number == "SCH1/NOAUTH001",
    ).first()

    assert student is None


def test_bulk_registration_rejects_duplicate_within_same_request(
    client,
    db,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "SCH1/SAME001",
                    "first_name": "First",
                    "last_name": "Student",
                },
                {
                    "admission_number": "SCH1/SAME001",
                    "first_name": "Second",
                    "last_name": "Student",
                },
            ],
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 2
    assert data["created"] == 1
    assert data["rejected"] == 1
    assert len(data["successes"]) == 1
    assert len(data["errors"]) == 1

    assert data["successes"][0]["row"] == 1
    assert data["errors"][0]["row"] == 2
    assert (
        data["errors"][0]["admission_number"]
        == "SCH1/SAME001"
    )

    students = db.query(Student).filter(
        Student.school_id == school_one_teacher.school_id,
        Student.admission_number == "SCH1/SAME001",
    ).all()

    assert len(students) == 1


def test_bulk_registration_can_reject_multiple_duplicates_and_continue(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": school_one_student.admission_number,
                    "first_name": "Existing",
                    "last_name": "One",
                },
                {
                    "admission_number": "SCH1/MIXED001",
                    "first_name": "Valid",
                    "last_name": "One",
                },
                {
                    "admission_number": school_one_student.admission_number,
                    "first_name": "Existing",
                    "last_name": "Two",
                },
                {
                    "admission_number": "SCH1/MIXED002",
                    "first_name": "Valid",
                    "last_name": "Two",
                },
            ],
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["submitted"] == 4
    assert data["created"] == 2
    assert data["rejected"] == 2

    assert [
        item["row"]
        for item in data["successes"]
    ] == [2, 4]

    assert [
        item["row"]
        for item in data["errors"]
    ] == [1, 3]

    for admission_number in [
        "SCH1/MIXED001",
        "SCH1/MIXED002",
    ]:
        student = db.query(Student).filter(
            Student.school_id == school_one_teacher.school_id,
            Student.admission_number == admission_number,
        ).one()

        enrollment = db.query(Enrollment).filter(
            Enrollment.student_id == student.id,
            Enrollment.class_id == school_one_class.id,
            Enrollment.academic_session_id
            == academic_session_one.id,
        ).one()

        assert enrollment.student_id == student.id


def test_registration_requires_at_least_one_student(
    client,
    db,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [],
        },
    )

    assert response.status_code == 422


def test_registration_validates_required_student_fields(
    client,
    db,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "SCH1/INVALID001",
                    "first_name": "A",
                    "last_name": "B",
                }
            ],
        },
    )

    assert response.status_code == 422

    student = db.query(Student).filter(
        Student.admission_number == "SCH1/INVALID001",
    ).first()

    assert student is None


def test_registration_preserves_optional_student_fields(
    client,
    db,
    school_one_teacher,
    school_one_class,
    academic_session_one,
):
    _assign_class_teacher(
        db,
        school_one_teacher,
        school_one_class,
        academic_session_one,
    )

    token = _login(client, school_one_teacher.user.email)

    response = client.post(
        "/api/students/class-teacher/register",
        headers=_auth(token),
        json={
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
            "students": [
                {
                    "admission_number": "SCH1/DETAIL001",
                    "first_name": "Khadijah",
                    "last_name": "Musa",
                    "date_of_birth": "2013-05-17",
                    "gender": "Female",
                }
            ],
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["created"] == 1
    assert data["rejected"] == 0

    student_data = data["successes"][0]["student"]

    assert student_data["date_of_birth"] == "2013-05-17"
    assert student_data["gender"] == "Female"

    student = db.query(Student).filter(
        Student.school_id == school_one_teacher.school_id,
        Student.admission_number == "SCH1/DETAIL001",
    ).one()

    assert student.date_of_birth.isoformat() == "2013-05-17"
    assert student.gender == "Female"