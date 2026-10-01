from app.models.enrollment import Enrollment
from app.models.student_score import StudentScore
from app.models.teaching_assignment import TeachingAssignment


def _login_headers(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200, response.text

    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def test_assigned_teacher_can_view_assessment_score_progress(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
):
    db.add_all(
        [
            TeachingAssignment(
                teacher_id=school_one_teacher.id,
                subject_id=school_one_subject.id,
                class_id=school_one_class.id,
                academic_session_id=academic_session_one.id,
            ),
            Enrollment(
                student_id=school_one_student.id,
                class_id=school_one_class.id,
                academic_session_id=academic_session_one.id,
            ),
        ]
    )
    db.commit()

    response = client.get(
        (
            "/api/student-scores/assessments/"
            f"{active_term_assessment.id}/progress"
        ),
        headers=_login_headers(client, "teacher.one@example.com"),
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "assessment_id": active_term_assessment.id,
        "total_students": 1,
        "scores_entered": 0,
        "scores_remaining": 1,
        "is_complete": False,
    }


def test_progress_counts_entered_scores_for_enrolled_students(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
):
    db.add_all(
        [
            TeachingAssignment(
                teacher_id=school_one_teacher.id,
                subject_id=school_one_subject.id,
                class_id=school_one_class.id,
                academic_session_id=academic_session_one.id,
            ),
            Enrollment(
                student_id=school_one_student.id,
                class_id=school_one_class.id,
                academic_session_id=academic_session_one.id,
            ),
        ]
    )
    db.flush()

    db.add(
        StudentScore(
            student_id=school_one_student.id,
            assessment_id=active_term_assessment.id,
            score=15,
        )
    )
    db.commit()

    response = client.get(
        (
            "/api/student-scores/assessments/"
            f"{active_term_assessment.id}/progress"
        ),
        headers=_login_headers(client, "teacher.one@example.com"),
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "assessment_id": active_term_assessment.id,
        "total_students": 1,
        "scores_entered": 1,
        "scores_remaining": 0,
        "is_complete": True,
    }


def test_assessment_with_no_enrolled_students_is_not_complete(
    client,
    db,
    school_one_teacher,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
):
    db.add(
        TeachingAssignment(
            teacher_id=school_one_teacher.id,
            subject_id=school_one_subject.id,
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
        )
    )
    db.commit()

    response = client.get(
        (
            "/api/student-scores/assessments/"
            f"{active_term_assessment.id}/progress"
        ),
        headers=_login_headers(client, "teacher.one@example.com"),
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "assessment_id": active_term_assessment.id,
        "total_students": 0,
        "scores_entered": 0,
        "scores_remaining": 0,
        "is_complete": False,
    }


def test_unassigned_teacher_cannot_view_assessment_score_progress(
    client,
    school_one_teacher,
    active_term_assessment,
):
    response = client.get(
        (
            "/api/student-scores/assessments/"
            f"{active_term_assessment.id}/progress"
        ),
        headers=_login_headers(client, "teacher.one@example.com"),
    )

    assert response.status_code == 403


def test_school_admin_can_view_assessment_score_progress(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    active_term_assessment,
):
    db.add(
        Enrollment(
            student_id=school_one_student.id,
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
        )
    )
    db.commit()

    response = client.get(
        (
            "/api/student-scores/assessments/"
            f"{active_term_assessment.id}/progress"
        ),
        headers=_login_headers(client, school_admin.email),
    )

    assert response.status_code == 200, response.text
    assert response.json()["total_students"] == 1
    assert response.json()["scores_entered"] == 0
    assert response.json()["is_complete"] is False


def test_unauthenticated_user_cannot_view_assessment_score_progress(
    client,
    active_term_assessment,
):
    response = client.get(
        (
            "/api/student-scores/assessments/"
            f"{active_term_assessment.id}/progress"
        )
    )

    assert response.status_code == 401