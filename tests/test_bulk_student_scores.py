from app.models.enrollment import Enrollment
from app.models.result_publication import ResultPublication
from app.models.student import Student
from app.models.student_score import StudentScore
from app.models.teaching_assignment import TeachingAssignment


def login_teacher(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "teacher.one@example.com",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def login_admin(client, school_admin):
    response = client.post(
        "/api/auth/login",
        json={
            "email": school_admin.email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_second_student(db, school_id):
    student = Student(
        user_id=None,
        school_id=school_id,
        admission_number="SCH1/002",
        first_name="Musa",
        last_name="Ali",
        date_of_birth=None,
        gender=None,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def assign_teacher(
    db,
    teacher_id,
    subject_id,
    class_id,
    academic_session_id,
):
    assignment = TeachingAssignment(
        teacher_id=teacher_id,
        subject_id=subject_id,
        class_id=class_id,
        academic_session_id=academic_session_id,
    )
    db.add(assignment)
    db.commit()
    return assignment


def enroll_student(
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
    return enrollment


def test_assigned_teacher_can_bulk_create_scores(
    client,
    db,
    school_one,
    school_one_teacher,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
    active_subscription,
):
    second_student = create_second_student(db, school_one.id)

    assign_teacher(
        db,
        school_one_teacher.id,
        school_one_subject.id,
        school_one_class.id,
        academic_session_one.id,
    )

    enroll_student(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    enroll_student(
        db,
        second_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    token = login_teacher(client)

    response = client.post(
        "/api/student-scores/bulk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assessment_id": active_term_assessment.id,
            "scores": [
                {
                    "student_id": school_one_student.id,
                    "score": 15,
                },
                {
                    "student_id": second_student.id,
                    "score": 18,
                },
            ],
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data) == 2

    saved_scores = {
        item["student_id"]: float(item["score"])
        for item in data
    }

    assert saved_scores[school_one_student.id] == 15.0
    assert saved_scores[second_student.id] == 18.0


def test_bulk_scores_create_and_update_in_same_request(
    client,
    db,
    school_one,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    active_term_assessment,
    active_subscription,
):
    second_student = create_second_student(db, school_one.id)

    enroll_student(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    enroll_student(
        db,
        second_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    existing_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=10,
    )
    db.add(existing_score)
    db.commit()

    token = login_admin(client, school_admin)

    response = client.post(
        "/api/student-scores/bulk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assessment_id": active_term_assessment.id,
            "scores": [
                {
                    "student_id": school_one_student.id,
                    "score": 17,
                },
                {
                    "student_id": second_student.id,
                    "score": 19,
                },
            ],
        },
    )

    assert response.status_code == 200, response.text

    db.refresh(existing_score)
    assert float(existing_score.score) == 17.0

    created_score = db.query(StudentScore).filter(
        StudentScore.student_id == second_student.id,
        StudentScore.assessment_id == active_term_assessment.id,
    ).one()

    assert float(created_score.score) == 19.0


def test_unassigned_teacher_cannot_bulk_save_scores(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    active_term_assessment,
    active_subscription,
):
    enroll_student(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    token = login_teacher(client)

    response = client.post(
        "/api/student-scores/bulk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assessment_id": active_term_assessment.id,
            "scores": [
                {
                    "student_id": school_one_student.id,
                    "score": 15,
                },
            ],
        },
    )

    assert response.status_code == 403, response.text

    saved_score = db.query(StudentScore).filter(
        StudentScore.student_id == school_one_student.id,
        StudentScore.assessment_id == active_term_assessment.id,
    ).first()

    assert saved_score is None


def test_bulk_scores_reject_out_of_range_score_without_partial_write(
    client,
    db,
    school_one,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    active_term_assessment,
    active_subscription,
):
    second_student = create_second_student(db, school_one.id)

    enroll_student(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )
    enroll_student(
        db,
        second_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    token = login_admin(client, school_admin)

    response = client.post(
        "/api/student-scores/bulk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assessment_id": active_term_assessment.id,
            "scores": [
                {
                    "student_id": school_one_student.id,
                    "score": 15,
                },
                {
                    "student_id": second_student.id,
                    "score": 25,
                },
            ],
        },
    )

    assert response.status_code == 400, response.text

    saved_scores = db.query(StudentScore).filter(
        StudentScore.assessment_id == active_term_assessment.id
    ).all()

    assert saved_scores == []


def test_bulk_scores_reject_non_enrolled_student_without_partial_write(
    client,
    db,
    school_one,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    active_term_assessment,
    active_subscription,
):
    non_enrolled_student = create_second_student(
        db,
        school_one.id,
    )

    enroll_student(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    token = login_admin(client, school_admin)

    response = client.post(
        "/api/student-scores/bulk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assessment_id": active_term_assessment.id,
            "scores": [
                {
                    "student_id": school_one_student.id,
                    "score": 15,
                },
                {
                    "student_id": non_enrolled_student.id,
                    "score": 18,
                },
            ],
        },
    )

    assert response.status_code == 400, response.text

    saved_scores = db.query(StudentScore).filter(
        StudentScore.assessment_id == active_term_assessment.id
    ).all()

    assert saved_scores == []


def test_bulk_scores_are_blocked_when_results_are_published(
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
    enroll_student(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    publication = ResultPublication(
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        status="published",
        published_by_user_id=school_admin.id,
    )
    db.add(publication)
    db.commit()

    token = login_admin(client, school_admin)

    response = client.post(
        "/api/student-scores/bulk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assessment_id": active_term_assessment.id,
            "scores": [
                {
                    "student_id": school_one_student.id,
                    "score": 15,
                },
            ],
        },
    )

    assert response.status_code == 409, response.text

    saved_score = db.query(StudentScore).filter(
        StudentScore.student_id == school_one_student.id,
        StudentScore.assessment_id == active_term_assessment.id,
    ).first()

    assert saved_score is None


def test_bulk_scores_require_active_subscription(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    pending_term_assessment,
):
    enroll_student(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    token = login_admin(client, school_admin)

    response = client.post(
        "/api/student-scores/bulk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assessment_id": pending_term_assessment.id,
            "scores": [
                {
                    "student_id": school_one_student.id,
                    "score": 15,
                },
            ],
        },
    )

    assert response.status_code == 403, response.text

    saved_score = db.query(StudentScore).filter(
        StudentScore.student_id == school_one_student.id,
        StudentScore.assessment_id == pending_term_assessment.id,
    ).first()

    assert saved_score is None


def test_bulk_scores_reject_duplicate_student_ids(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    academic_session_one,
    active_term_assessment,
    active_subscription,
):
    enroll_student(
        db,
        school_one_student.id,
        school_one_class.id,
        academic_session_one.id,
    )

    token = login_admin(client, school_admin)

    response = client.post(
        "/api/student-scores/bulk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assessment_id": active_term_assessment.id,
            "scores": [
                {
                    "student_id": school_one_student.id,
                    "score": 15,
                },
                {
                    "student_id": school_one_student.id,
                    "score": 18,
                },
            ],
        },
    )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == (
        "Duplicate student IDs are not allowed"
    )

    saved_score = db.query(StudentScore).filter(
        StudentScore.student_id == school_one_student.id,
        StudentScore.assessment_id == active_term_assessment.id,
    ).first()

    assert saved_score is None


def test_bulk_scores_reject_empty_score_list(
    client,
    school_admin,
    active_term_assessment,
):
    token = login_admin(client, school_admin)

    response = client.post(
        "/api/student-scores/bulk",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "assessment_id": active_term_assessment.id,
            "scores": [],
        },
    )

    assert response.status_code == 422, response.text
