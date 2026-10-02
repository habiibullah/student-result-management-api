from sqlalchemy import select
from app.models.academic_session import AcademicSession
from app.models.class_model import Class
from app.models.class_teacher_assignment import ClassTeacherAssignment
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.term_report_comment import TermReportComment


PASSWORD = "TestPassword123!"


def login(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_assignment(
    db,
    teacher_id,
    class_id,
    academic_session_id,
):
    assignment = ClassTeacherAssignment(
        teacher_id=teacher_id,
        class_id=class_id,
        academic_session_id=academic_session_id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def create_enrollment(
    db,
    student_id,
    class_id,
    academic_session_id,
):
    enrollment = Enrollment(
        student_id=student_id,
        class_id=class_id,
        academic_session_id=academic_session_id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def create_comment(
    db,
    student_id,
    academic_session_id,
    term_id,
    teacher_comment="Existing teacher comment.",
    principal_comment="Existing principal comment.",
):
    comment = TermReportComment(
        student_id=student_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        teacher_comment=teacher_comment,
        principal_comment=principal_comment,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def create_second_class(db, school):
    class_ = Class(
        school_id=school.id,
        name="Second Class",
        code="SECOND-CT",
        description="Second class for report comment tests",
    )
    db.add(class_)
    db.commit()
    db.refresh(class_)
    return class_


def create_second_session(db, school):
    session = AcademicSession(
        school_id=school.id,
        name="2027/2028",
        is_current=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def test_assigned_class_teacher_can_create_teacher_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.post(
        "/api/term-report-comments/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "teacher_comment": "A very good term.",
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["teacher_comment"] == "A very good term."
    assert data["principal_comment"] is None


def test_class_teacher_payload_cannot_set_principal_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.post(
        "/api/term-report-comments/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "teacher_comment": "Teacher comment.",
            "principal_comment": "Teacher must not set this.",
        },
    )

    assert response.status_code == 422

    comment = db.scalar(
        select(TermReportComment).where(
            TermReportComment.student_id == school_one_student.id,
            TermReportComment.academic_session_id == academic_session_one.id,
            TermReportComment.term_id == first_term.id,
         )
    )

    assert comment is None

def test_assigned_class_teacher_can_read_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.get(
        f"/api/term-report-comments/class-teacher/{comment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == comment.id


def test_assigned_class_teacher_can_update_teacher_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.patch(
        f"/api/term-report-comments/class-teacher/{comment.id}",
        headers=auth_headers(token),
        json={
            "teacher_comment": "Updated by the class teacher.",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["teacher_comment"] == (
        "Updated by the class teacher."
    )
    assert response.json()["principal_comment"] == (
        "Existing principal comment."
    )


def test_class_teacher_update_cannot_modify_principal_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.patch(
        f"/api/term-report-comments/class-teacher/{comment.id}",
        headers=auth_headers(token),
        json={
            "teacher_comment": "Updated teacher comment.",
            "principal_comment": "Compromised principal comment.",
        },
    )

    assert response.status_code == 422

    db.refresh(comment)

    assert comment.teacher_comment == "Existing teacher comment."
    assert comment.principal_comment == "Existing principal comment."

def test_class_teacher_list_contains_assigned_student_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.get(
        "/api/term-report-comments/class-teacher",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    returned_ids = {item["id"] for item in response.json()}
    assert comment.id in returned_ids


def test_class_teacher_list_excludes_other_class_comment(
    client,
    db,
    school_one,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    second_class = create_second_class(db, school_one)

    second_student = Student(
        school_id=school_one.id,
        admission_number="CT-OTHER-001",
        first_name="Other",
        last_name="Student",
        gender="male",
    )
    db.add(second_student)
    db.commit()
    db.refresh(second_student)

    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )

    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        second_student.id,
        second_class.id,
        academic_session_one.id,
    )

    own_comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )
    other_comment = create_comment(
        db,
        second_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.get(
        "/api/term-report-comments/class-teacher",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    returned_ids = {item["id"] for item in response.json()}

    assert own_comment.id in returned_ids
    assert other_comment.id not in returned_ids


def test_unassigned_teacher_cannot_create_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.post(
        "/api/term-report-comments/class-teacher",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "academic_session_id": academic_session_one.id,
            "term_id": first_term.id,
            "teacher_comment": "Unauthorized comment.",
        },
    )

    assert response.status_code == 403


def test_unassigned_teacher_cannot_read_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.get(
        f"/api/term-report-comments/class-teacher/{comment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_unassigned_teacher_cannot_update_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.patch(
        f"/api/term-report-comments/class-teacher/{comment.id}",
        headers=auth_headers(token),
        json={"teacher_comment": "Unauthorized update."},
    )

    assert response.status_code == 403


def test_teacher_assigned_to_wrong_class_cannot_update_comment(
    client,
    db,
    school_one,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    second_class = create_second_class(db, school_one)

    create_assignment(
        db,
        school_one_teacher.id,
        second_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.patch(
        f"/api/term-report-comments/class-teacher/{comment.id}",
        headers=auth_headers(token),
        json={"teacher_comment": "Wrong class update."},
    )

    assert response.status_code == 403


def test_wrong_session_assignment_does_not_grant_access(
    client,
    db,
    school_one,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    second_session = create_second_session(db, school_one)

    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        second_session.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.get(
        f"/api/term-report-comments/class-teacher/{comment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_class_teacher_historical_comment_remains_readable(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    active_subscription.status = "expired"
    db.commit()

    token = login(client, "teacher.one@example.com")

    response = client.get(
        f"/api/term-report-comments/class-teacher/{comment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == comment.id


def test_inactive_subscription_blocks_class_teacher_update(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    second_term,
    pending_subscription,
):
    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        second_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.patch(
        f"/api/term-report-comments/class-teacher/{comment.id}",
        headers=auth_headers(token),
        json={"teacher_comment": "Blocked update."},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "An active subscription is required "
        "for this academic term"
    )


def test_teacher_cannot_delete_report_comment(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_assignment(
        db,
        school_one_teacher.id,
        school_one_class.id,
        academic_session_one.id,
    )
    create_enrollment(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    comment = create_comment(
        db,
        school_one_student.id,
        academic_session_one.id,
        first_term.id,
    )

    token = login(client, "teacher.one@example.com")

    response = client.delete(
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 403
