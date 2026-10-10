from app.models import (
    Enrollment,
    PublishedReportSnapshot,
    ResultPublication,
    Student,
    StudentAttendance,
    StudentBehaviouralAssessment,
    StudentScore,
    TermReportComment,
)


def login(client, email, password="TestPassword123!"):
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

def test_student_without_academic_records_can_be_deleted(
    client,
    db,
    school_admin,
    school_one_student,
):
    student_id = school_one_student.id

    token = login(client, school_admin.email)

    response = client.delete(
        f"/api/students/{student_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204

    db.expire_all()
    assert db.get(Student, student_id) is None


def test_cross_school_student_deletion_is_blocked(
    client,
    db,
    school_admin,
    school_two_student,
):
    student_id = school_two_student.id

    token = login(client, school_admin.email)

    response = client.delete(
        f"/api/students/{student_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found"

    db.expire_all()
    assert db.get(Student, student_id) is not None


def test_student_with_attendance_cannot_be_deleted(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
):
    attendance = StudentAttendance(
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        school_days=100,
        days_present=90,
        days_absent=10,
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    student_id = school_one_student.id
    attendance_id = attendance.id

    token = login(client, school_admin.email)

    response = client.delete(
        f"/api/students/{student_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert "academic records exist" in response.json()["detail"]

    db.expire_all()

    assert db.get(Student, student_id) is not None
    assert db.get(StudentAttendance, attendance_id) is not None

def test_student_with_score_cannot_be_deleted(
    client,
    db,
    school_admin,
    school_one_student,
    active_term_assessment,
):
    score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=15,
    )

    db.add(score)
    db.commit()
    db.refresh(score)

    student_id = school_one_student.id
    score_id = score.id

    token = login(client, school_admin.email)

    response = client.delete(
        f"/api/students/{student_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert "academic records exist" in response.json()["detail"]

    db.expire_all()

    assert db.get(Student, student_id) is not None
    assert db.get(StudentScore, score_id) is not None


def test_student_with_behavioural_assessment_cannot_be_deleted(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
):
    assessment = StudentBehaviouralAssessment(
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        punctuality=5,
        neatness=4,
        honesty=5,
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    student_id = school_one_student.id
    assessment_id = assessment.id

    token = login(client, school_admin.email)

    response = client.delete(
        f"/api/students/{student_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert "academic records exist" in response.json()["detail"]

    db.expire_all()

    assert db.get(Student, student_id) is not None
    assert (
        db.get(StudentBehaviouralAssessment, assessment_id)
        is not None
    )


def test_student_with_report_comment_cannot_be_deleted(
    client,
    db,
    school_admin,
    school_one_student,
    academic_session_one,
    first_term,
):
    comment = TermReportComment(
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        teacher_comment="Excellent progress.",
        principal_comment="Keep improving.",
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    student_id = school_one_student.id
    comment_id = comment.id

    token = login(client, school_admin.email)

    response = client.delete(
        f"/api/students/{student_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert "academic records exist" in response.json()["detail"]

    db.expire_all()

    assert db.get(Student, student_id) is not None
    assert db.get(TermReportComment, comment_id) is not None

def test_student_with_enrollment_cannot_be_deleted(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
):
    enrollment = Enrollment(
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    student_id = school_one_student.id
    enrollment_id = enrollment.id

    token = login(client, school_admin.email)

    response = client.delete(
        f"/api/students/{student_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert "enrollments" in response.json()["detail"]

    db.expire_all()

    assert db.get(Student, student_id) is not None
    assert db.get(Enrollment, enrollment_id) is not None

def test_student_with_published_snapshot_cannot_be_deleted(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    publication = ResultPublication(
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        status="published",
        published_by_user_id=school_admin.id,
    )

    db.add(publication)
    db.commit()
    db.refresh(publication)

    snapshot = PublishedReportSnapshot(
        publication_id=publication.id,
        student_id=school_one_student.id,
        report_data={"student_id": school_one_student.id},
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    student_id = school_one_student.id
    snapshot_id = snapshot.id

    token = login(client, school_admin.email)

    response = client.delete(
        f"/api/students/{student_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert "academic records exist" in response.json()["detail"]

    db.expire_all()

    assert db.get(Student, student_id) is not None
    assert db.get(PublishedReportSnapshot, snapshot_id) is not None