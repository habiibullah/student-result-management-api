from app.models.assessment import Assessment
from app.models.subject import Subject
from app.models.teaching_assignment import TeachingAssignment


def test_teacher_sees_only_assigned_assessments_and_admin_sees_both(
    client,
    db,
    school_one_teacher,
    school_admin,
    school_one_class,
    school_one_subject,
    academic_session_one,
    active_term_assessment,
    second_term,
):
    other_subject = Subject(
        school_id=school_one_subject.school_id,
        name="Chemistry",
        code="CHEM",
        description="Unassigned test subject",
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

    assignment = TeachingAssignment(
        teacher_id=school_one_teacher.id,
        subject_id=school_one_subject.id,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
    )

    db.add_all([other_assessment, assignment])
    db.commit()

    def get_assessments_for(email):
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/assessments",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, response.text
        return {item["id"] for item in response.json()}

    teacher_ids = get_assessments_for("teacher.one@example.com")
    assert active_term_assessment.id in teacher_ids
    assert other_assessment.id not in teacher_ids

    admin_ids = get_assessments_for(school_admin.email)
    assert active_term_assessment.id in admin_ids
    assert other_assessment.id in admin_ids
