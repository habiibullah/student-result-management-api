from app.models.enrollment import Enrollment
from app.models.result_publication import ResultPublication
from app.models.student_attendance import StudentAttendance
from app.models.student_score import StudentScore
from app.models.term_report_comment import TermReportComment


# ============================================================
# AUTH HELPERS
# ============================================================


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


# ============================================================
# ASSERTION HELPERS
# ============================================================


def assert_result_locked(response):
    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Results for this class and term are published "
        "and cannot be modified. Reopen the results first."
    )


def assert_enrollment_locked(response):
    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Published results exist for this class and "
        "academic session. Enrollment records cannot "
        "be modified until the published results are reopened."
    )


# ============================================================
# DATABASE HELPERS
# ============================================================


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


def create_score(
    db,
    student_id,
    assessment_id,
    score=8,
):
    student_score = StudentScore(
        student_id=student_id,
        assessment_id=assessment_id,
        score=score,
    )

    db.add(student_score)
    db.commit()
    db.refresh(student_score)

    return student_score


def create_attendance(
    db,
    student_id,
    academic_session_id,
    term_id,
):
    attendance = StudentAttendance(
        student_id=student_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        school_days=60,
        days_present=55,
        days_absent=5,
    )

    db.add(attendance)
    db.commit()
    db.refresh(attendance)

    return attendance


def create_comment(
    db,
    student_id,
    academic_session_id,
    term_id,
):
    comment = TermReportComment(
        student_id=student_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        teacher_comment="Good performance.",
        principal_comment="Keep improving.",
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


def create_publication(
    db,
    class_id,
    academic_session_id,
    term_id,
    published_by_user_id,
    publication_status="published",
):
    publication = ResultPublication(
        class_id=class_id,
        academic_session_id=academic_session_id,
        term_id=term_id,
        status=publication_status,
        published_by_user_id=published_by_user_id,
    )

    db.add(publication)
    db.commit()
    db.refresh(publication)

    return publication


# ============================================================
# ASSESSMENT LOCKS
# ============================================================


def test_published_result_blocks_assessment_update(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
    first_term,
    active_term_assessment,
    active_subscription,
):
    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/assessments/{active_term_assessment.id}",
        headers=auth_headers(token),
        json={
            "name": "Updated CA 1",
        },
    )

    assert_result_locked(response)


def test_published_result_blocks_assessment_delete(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
    first_term,
    active_term_assessment,
    active_subscription,
):
    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/assessments/{active_term_assessment.id}",
        headers=auth_headers(token),
    )

    assert_result_locked(response)


# ============================================================
# STUDENT SCORE LOCKS
# ============================================================


def test_published_result_blocks_score_update(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_term_assessment,
    active_subscription,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=8,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/student-scores/{score.id}",
        headers=auth_headers(token),
        json={
            "score": 9,
        },
    )

    assert_result_locked(response)


def test_published_result_blocks_score_delete(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_term_assessment,
    active_subscription,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=8,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/student-scores/{score.id}",
        headers=auth_headers(token),
    )

    assert_result_locked(response)


# ============================================================
# ATTENDANCE LOCKS
# ============================================================


def test_published_result_blocks_attendance_update(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    attendance = create_attendance(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/student-attendance/{attendance.id}",
        headers=auth_headers(token),
        json={
            "school_days": 60,
            "days_present": 56,
            "days_absent": 4,
        },
    )

    assert_result_locked(response)


def test_published_result_blocks_attendance_delete(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    attendance = create_attendance(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/student-attendance/{attendance.id}",
        headers=auth_headers(token),
    )

    assert_result_locked(response)


# ============================================================
# TERM REPORT COMMENT LOCKS
# ============================================================


def test_published_result_blocks_comment_update(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    comment = create_comment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
        json={
            "teacher_comment": (
                "This comment should not be allowed."
            ),
        },
    )

    assert_result_locked(response)


def test_published_result_blocks_comment_delete(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    comment = create_comment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
    )

    assert_result_locked(response)


# ============================================================
# ENROLLMENT LOCKS
# ============================================================


def test_published_result_blocks_enrollment_create(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/enrollments",
        headers=auth_headers(token),
        json={
            "student_id": school_one_student.id,
            "class_id": school_one_class.id,
            "academic_session_id": academic_session_one.id,
        },
    )

    assert_enrollment_locked(response)


def test_published_result_blocks_enrollment_update(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    enrollment = create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/enrollments/{enrollment.id}",
        headers=auth_headers(token),
        json={
            "class_id": school_one_class.id,
        },
    )

    assert_enrollment_locked(response)


def test_published_result_blocks_enrollment_delete(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    enrollment = create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/enrollments/{enrollment.id}",
        headers=auth_headers(token),
    )

    assert_enrollment_locked(response)


# ============================================================
# REOPENED RESULTS
# ============================================================


def test_reopened_result_allows_assessment_update(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
    first_term,
    active_term_assessment,
    active_subscription,
):
    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
        publication_status="reopened",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/assessments/{active_term_assessment.id}",
        headers=auth_headers(token),
        json={
            "name": "Corrected CA 1",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Corrected CA 1"


def test_reopened_result_allows_score_update(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_term_assessment,
    active_subscription,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    score = create_score(
        db=db,
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=8,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
        publication_status="reopened",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/student-scores/{score.id}",
        headers=auth_headers(token),
        json={
            "score": 9,
        },
    )

    assert response.status_code == 200
    assert float(response.json()["score"]) == 9.0


def test_reopened_result_allows_attendance_update(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    attendance = create_attendance(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
        publication_status="reopened",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/student-attendance/{attendance.id}",
        headers=auth_headers(token),
        json={
            "school_days": 60,
            "days_present": 56,
            "days_absent": 4,
        },
    )

    assert response.status_code == 200
    assert response.json()["days_present"] == 56
    assert response.json()["days_absent"] == 4


def test_reopened_result_allows_comment_update(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    comment = create_comment(
        db=db,
        student_id=school_one_student.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
        publication_status="reopened",
    )

    token = login(
        client,
        school_admin.email,
    )

    corrected_comment = (
        "Corrected teacher comment after reopening."
    )

    response = client.patch(
        f"/api/term-report-comments/{comment.id}",
        headers=auth_headers(token),
        json={
            "teacher_comment": corrected_comment,
        },
    )

    assert response.status_code == 200
    assert response.json()["teacher_comment"] == (
        corrected_comment
    )


def test_reopened_result_allows_enrollment_update(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    enrollment = create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
        publication_status="reopened",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        f"/api/enrollments/{enrollment.id}",
        headers=auth_headers(token),
        json={
            "class_id": school_one_class.id,
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == enrollment.id


def test_reopened_result_allows_enrollment_delete(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    first_term,
):
    enrollment = create_enrollment(
        db=db,
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
        publication_status="reopened",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.delete(
        f"/api/enrollments/{enrollment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 204
