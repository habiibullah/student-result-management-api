from app.models.enrollment import Enrollment
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


def test_assigned_teacher_can_list_enrolled_assessment_students(
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
        f"/api/student-scores/assessments/{active_term_assessment.id}/students",
        headers=_login_headers(client, "teacher.one@example.com"),
    )

    assert response.status_code == 200, response.text
    assert response.json() == [
        {
            "id": school_one_student.id,
            "admission_number": school_one_student.admission_number,
            "first_name": school_one_student.first_name,
            "last_name": school_one_student.last_name,
        }
    ]


def test_unassigned_teacher_cannot_list_assessment_students(
    client,
    db,
    school_one_teacher,
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
        f"/api/student-scores/assessments/{active_term_assessment.id}/students",
        headers=_login_headers(client, "teacher.one@example.com"),
    )

    assert response.status_code == 403, response.text


def test_school_admin_can_list_assessment_students(
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
        f"/api/student-scores/assessments/{active_term_assessment.id}/students",
        headers=_login_headers(client, school_admin.email),
    )

    assert response.status_code == 200, response.text
    assert [student["id"] for student in response.json()] == [
        school_one_student.id
    ]
