from app.models.enrollment import Enrollment
from app.models.teaching_assignment import TeachingAssignment


def test_assigned_teacher_can_create_student_score(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
    active_subscription,
):
    assignment = TeachingAssignment(
        teacher_id=school_one_teacher.id,
        subject_id=school_one_subject.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    enrollment = Enrollment(
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    db.add_all([assignment, enrollment])
    db.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "teacher.one@example.com",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/student-scores",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_id": school_one_student.id,
            "assessment_id": active_term_assessment.id,
            "score": 15,
        },
    )

    assert response.status_code == 201, response.text
    assert float(response.json()["score"]) == 15.0


def test_unassigned_teacher_cannot_create_student_score(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    academic_session_one,
    active_term_assessment,
    active_subscription,
):
    enrollment = Enrollment(
        student_id=school_one_student.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    db.add(enrollment)
    db.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "teacher.one@example.com",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/student-scores",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "student_id": school_one_student.id,
            "assessment_id": active_term_assessment.id,
            "score": 15,
        },
    )

    assert response.status_code == 403, response.text


def test_assigned_teacher_can_view_student_score(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
):
    from app.models.student_score import StudentScore

    assignment = TeachingAssignment(
        teacher_id=school_one_teacher.id,
        subject_id=school_one_subject.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    student_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=15,
    )

    db.add_all([assignment, student_score])
    db.commit()
    db.refresh(student_score)

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "teacher.one@example.com",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        f"/api/student-scores/{student_score.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == student_score.id
    assert float(response.json()["score"]) == 15.0


def test_unassigned_teacher_cannot_view_student_score(
    client,
    db,
    school_one_teacher,
    school_one_student,
    active_term_assessment,
):
    from app.models.student_score import StudentScore

    student_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=15,
    )

    db.add(student_score)
    db.commit()
    db.refresh(student_score)

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "teacher.one@example.com",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        f"/api/student-scores/{student_score.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403, response.text


def test_teacher_score_list_contains_only_assigned_assessments(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
    second_term,
):
    from app.models.assessment import Assessment
    from app.models.student_score import StudentScore
    from app.models.subject import Subject

    assignment = TeachingAssignment(
        teacher_id=school_one_teacher.id,
        subject_id=school_one_subject.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    other_subject = Subject(
        school_id=school_one_subject.school_id,
        name="Chemistry",
        code="CHEM",
        description="Unassigned test subject",
    )
    db.add(other_subject)
    db.flush()

    unassigned_assessment = Assessment(
        class_id=school_one_class.id,
        subject_id=other_subject.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
        assessment_type="CA",
        sequence=2,
        name="Unassigned Test CA",
        max_score=20,
    )

    db.add_all([assignment, unassigned_assessment])
    db.flush()

    assigned_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=15,
    )

    other_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=unassigned_assessment.id,
        score=12,
    )

    db.add_all([assigned_score, other_score])
    db.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "teacher.one@example.com",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/student-scores",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    returned_ids = {item["id"] for item in response.json()}

    assert assigned_score.id in returned_ids
    assert other_score.id not in returned_ids


def test_school_admin_can_list_scores_across_subjects(
    client,
    db,
    school_admin,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
    second_term,
):
    from app.models.assessment import Assessment
    from app.models.student_score import StudentScore
    from app.models.subject import Subject

    other_subject = Subject(
        school_id=school_one_subject.school_id,
        name="Chemistry",
        code="CHEM",
        description="Second test subject",
    )

    db.add(other_subject)
    db.flush()

    other_assessment = Assessment(
        class_id=school_one_class.id,
        subject_id=other_subject.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
        assessment_type="CA",
        sequence=2,
        name="Chemistry Test CA",
        max_score=20,
    )

    db.add(other_assessment)
    db.flush()

    physics_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=15,
    )

    chemistry_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=other_assessment.id,
        score=12,
    )

    db.add_all([physics_score, chemistry_score])
    db.commit()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": school_admin.email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/student-scores",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text

    returned_ids = {item["id"] for item in response.json()}

    assert physics_score.id in returned_ids
    assert chemistry_score.id in returned_ids


def test_assigned_teacher_can_update_student_score(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
    active_subscription,
):
    from app.models.student_score import StudentScore

    assignment = TeachingAssignment(
        teacher_id=school_one_teacher.id,
        subject_id=school_one_subject.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    student_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=15,
    )

    db.add_all([assignment, student_score])
    db.commit()
    db.refresh(student_score)

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "teacher.one@example.com",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/api/student-scores/{student_score.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"score": 18},
    )

    assert response.status_code == 200, response.text
    assert float(response.json()["score"]) == 18.0

    db.refresh(student_score)
    assert float(student_score.score) == 18.0


def test_unassigned_teacher_cannot_update_student_score(
    client,
    db,
    school_one_teacher,
    school_one_student,
    active_term_assessment,
    active_subscription,
):
    from app.models.student_score import StudentScore

    student_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=15,
    )

    db.add(student_score)
    db.commit()
    db.refresh(student_score)

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "teacher.one@example.com",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.patch(
        f"/api/student-scores/{student_score.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"score": 18},
    )

    assert response.status_code == 403, response.text

    db.refresh(student_score)
    assert float(student_score.score) == 15.0


def test_teacher_cannot_delete_student_score(
    client,
    db,
    school_one_teacher,
    school_one_student,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
):
    from app.models.student_score import StudentScore

    assignment = TeachingAssignment(
        teacher_id=school_one_teacher.id,
        subject_id=school_one_subject.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    student_score = StudentScore(
        student_id=school_one_student.id,
        assessment_id=active_term_assessment.id,
        score=15,
    )

    db.add_all([assignment, student_score])
    db.commit()
    db.refresh(student_score)

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "teacher.one@example.com",
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.delete(
        f"/api/student-scores/{student_score.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403, response.text

    db.refresh(student_score)
    assert float(student_score.score) == 15.0
