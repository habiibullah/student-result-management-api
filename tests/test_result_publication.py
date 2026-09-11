from copy import deepcopy

from app.models.assessment import Assessment
from app.models.enrollment import Enrollment
from app.models.published_report_snapshot import PublishedReportSnapshot
from app.models.result_publication import ResultPublication
from app.models.student_score import StudentScore


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


def publication_payload(
    class_id,
    academic_session_id,
    term_id,
):
    return {
        "class_id": class_id,
        "academic_session_id": academic_session_id,
        "term_id": term_id,
    }


def assert_subscription_required(response):
    assert response.status_code == 403

    assert response.json()["detail"] == (
        "An active subscription is required "
        "for this academic term"
    )


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


def prepare_complete_result(
    db,
    student,
    class_record,
    academic_session,
    assessment,
    score=8,
):
    enrollment = create_enrollment(
        db=db,
        student_id=student.id,
        class_id=class_record.id,
        academic_session_id=academic_session.id,
    )

    ca1_score = create_score(
        db=db,
        student_id=student.id,
        assessment_id=assessment.id,
        score=score,
    )

    ca2 = Assessment(
        class_id=class_record.id,
        subject_id=assessment.subject_id,
        academic_session_id=academic_session.id,
        term_id=assessment.term_id,
        assessment_type="CA",
        sequence=2,
        name="CA 2",
        max_score=10,
    )

    ca3 = Assessment(
        class_id=class_record.id,
        subject_id=assessment.subject_id,
        academic_session_id=academic_session.id,
        term_id=assessment.term_id,
        assessment_type="CA",
        sequence=3,
        name="CA 3",
        max_score=10,
    )

    exam = Assessment(
        class_id=class_record.id,
        subject_id=assessment.subject_id,
        academic_session_id=academic_session.id,
        term_id=assessment.term_id,
        assessment_type="EXAM",
        sequence=1,
        name="Examination",
        max_score=70,
    )

    db.add_all(
        [
            ca2,
            ca3,
            exam,
        ]
    )
    db.commit()

    db.refresh(ca2)
    db.refresh(ca3)
    db.refresh(exam)

    create_score(
        db=db,
        student_id=student.id,
        assessment_id=ca2.id,
        score=7,
    )

    create_score(
        db=db,
        student_id=student.id,
        assessment_id=ca3.id,
        score=9,
    )

    create_score(
        db=db,
        student_id=student.id,
        assessment_id=exam.id,
        score=58,
    )

    return enrollment, ca1_score


# ============================================================
# SUCCESSFUL PUBLICATION
# ============================================================


def test_complete_result_can_be_published(
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
    prepare_complete_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        academic_session=academic_session_one,
        assessment=active_term_assessment,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["class_id"] == school_one_class.id
    assert data["academic_session_id"] == (
        academic_session_one.id
    )
    assert data["term_id"] == first_term.id
    assert data["status"] == "published"
    assert data["published_by_user_id"] == (
        school_admin.id
    )


# ============================================================
# SNAPSHOT CREATION
# ============================================================


def test_publication_creates_student_report_snapshot(
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
    prepare_complete_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        academic_session=academic_session_one,
        assessment=active_term_assessment,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        ),
    )

    assert response.status_code == 201

    publication_id = response.json()["id"]

    snapshot = db.query(
        PublishedReportSnapshot
    ).filter(
        PublishedReportSnapshot.publication_id
        == publication_id,
        PublishedReportSnapshot.student_id
        == school_one_student.id,
    ).one_or_none()

    assert snapshot is not None
    assert snapshot.report_data is not None

    report_data = snapshot.report_data

    assert report_data["student"]["student_id"] == (
        school_one_student.id
    )

    assert report_data["class_info"]["class_id"] == (
        school_one_class.id
    )

    assert report_data["term_info"]["term_id"] == (
        first_term.id
    )

    assert (
        report_data["performance"]["result_status"]
        == "COMPLETE"
    )


# ============================================================
# READINESS
# ============================================================


def test_publication_rejected_when_class_has_no_enrollment(
    client,
    school_admin,
    school_one_class,
    academic_session_one,
    first_term,
    active_term_assessment,
    active_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Cannot publish results because the class "
        "has no enrolled students for this session"
    )


def test_incomplete_result_cannot_be_published(
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

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        ),
    )

    assert response.status_code == 400

    detail = response.json()["detail"]

    assert detail["message"] == (
        "Cannot publish results because some "
        "student results are incomplete"
    )

    assert school_one_student.id in (
        detail["incomplete_student_ids"]
    )


# ============================================================
# SUBSCRIPTION ENFORCEMENT
# ============================================================


def test_pending_subscription_blocks_publication(
    client,
    school_admin,
    school_one_class,
    academic_session_one,
    second_term,
    pending_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
            term_id=second_term.id,
        ),
    )

    assert_subscription_required(response)


def test_cancelled_subscription_blocks_publication(
    client,
    school_admin,
    school_one_class,
    academic_session_one,
    third_term,
    cancelled_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
            term_id=third_term.id,
        ),
    )

    assert_subscription_required(response)


def test_expired_subscription_blocks_publication(
    client,
    school_admin,
    school_one_class,
    academic_session_one,
    test_extra_term,
    expired_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
            term_id=test_extra_term.id,
        ),
    )

    assert_subscription_required(response)


def test_missing_subscription_blocks_publication(
    client,
    school_admin,
    school_one_class,
    academic_session_one,
    unsubscribed_term,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
            term_id=unsubscribed_term.id,
        ),
    )

    assert_subscription_required(response)


# ============================================================
# DUPLICATE PUBLICATION
# ============================================================


def test_already_published_result_cannot_be_published_again(
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
    prepare_complete_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        academic_session=academic_session_one,
        assessment=active_term_assessment,
    )

    token = login(
        client,
        school_admin.email,
    )

    payload = publication_payload(
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    first_response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=payload,
    )

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == (
        "Results are already published for this "
        "class, session and term"
    )


# ============================================================
# READ PUBLICATIONS
# ============================================================


def test_school_admin_can_read_own_publication(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
    first_term,
):
    publication = create_publication(
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

    response = client.get(
        f"/api/result-publications/{publication.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == publication.id


def test_publication_list_contains_only_own_school(
    client,
    db,
    school_admin,
    other_school_admin,
    school_one_class,
    school_two_class,
    academic_session_one,
    academic_session_two,
    first_term,
    school_two_term,
):
    own_publication = create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
        published_by_user_id=school_admin.id,
    )

    other_publication = create_publication(
        db=db,
        class_id=school_two_class.id,
        academic_session_id=academic_session_two.id,
        term_id=school_two_term.id,
        published_by_user_id=other_school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/result-publications",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        publication["id"]
        for publication in response.json()
    }

    assert own_publication.id in returned_ids
    assert other_publication.id not in returned_ids


# ============================================================
# CROSS-SCHOOL ISOLATION
# ============================================================


def test_school_admin_cannot_read_other_school_publication(
    client,
    db,
    school_admin,
    other_school_admin,
    school_two_class,
    academic_session_two,
    school_two_term,
):
    publication = create_publication(
        db=db,
        class_id=school_two_class.id,
        academic_session_id=academic_session_two.id,
        term_id=school_two_term.id,
        published_by_user_id=other_school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/result-publications/{publication.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Result publication not found"
    )


def test_school_admin_cannot_publish_other_school_results(
    client,
    school_admin,
    school_two_class,
    academic_session_two,
    school_two_term,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_two_class.id,
            academic_session_id=academic_session_two.id,
            term_id=school_two_term.id,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Class not found"


# ============================================================
# REOPENING
# ============================================================


def test_published_result_can_be_reopened(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    publication = create_publication(
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
        (
            f"/api/result-publications/"
            f"{publication.id}/reopen"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "reopened"


def test_already_reopened_result_cannot_be_reopened_again(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
    first_term,
    active_subscription,
):
    publication = create_publication(
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
        (
            f"/api/result-publications/"
            f"{publication.id}/reopen"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Results are already reopened"
    )


def test_inactive_subscription_blocks_reopening(
    client,
    db,
    school_admin,
    school_one_class,
    academic_session_one,
    second_term,
    pending_subscription,
):
    publication = create_publication(
        db=db,
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=second_term.id,
        published_by_user_id=school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            f"/api/result-publications/"
            f"{publication.id}/reopen"
        ),
        headers=auth_headers(token),
    )

    assert_subscription_required(response)


def test_school_admin_cannot_reopen_other_school_publication(
    client,
    db,
    school_admin,
    other_school_admin,
    school_two_class,
    academic_session_two,
    school_two_term,
    school_two_subscription,
):
    publication = create_publication(
        db=db,
        class_id=school_two_class.id,
        academic_session_id=academic_session_two.id,
        term_id=school_two_term.id,
        published_by_user_id=other_school_admin.id,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            f"/api/result-publications/"
            f"{publication.id}/reopen"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Result publication not found"
    )


# ============================================================
# REPUBLISHING / SNAPSHOT REFRESH
# ============================================================


def test_republish_reuses_publication_and_snapshot(
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
    _, student_score = prepare_complete_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        academic_session=academic_session_one,
        assessment=active_term_assessment,
        score=8,
    )

    token = login(
        client,
        school_admin.email,
    )

    payload = publication_payload(
        class_id=school_one_class.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    first_publish = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=payload,
    )

    assert first_publish.status_code == 201

    publication_id = first_publish.json()["id"]

    first_snapshot = db.query(
        PublishedReportSnapshot
    ).filter(
        PublishedReportSnapshot.publication_id
        == publication_id,
        PublishedReportSnapshot.student_id
        == school_one_student.id,
    ).one()

    snapshot_id = first_snapshot.id

    original_report = deepcopy(
        first_snapshot.report_data
    )

    reopen_response = client.patch(
        (
            f"/api/result-publications/"
            f"{publication_id}/reopen"
        ),
        headers=auth_headers(token),
    )

    assert reopen_response.status_code == 200
    assert reopen_response.json()["status"] == "reopened"

    student_score.score = 9
    db.commit()

    second_publish = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=payload,
    )

    assert second_publish.status_code == 201
    assert second_publish.json()["id"] == publication_id
    assert second_publish.json()["status"] == "published"

    db.expire_all()

    refreshed_snapshot = db.query(
        PublishedReportSnapshot
    ).filter(
        PublishedReportSnapshot.publication_id
        == publication_id,
        PublishedReportSnapshot.student_id
        == school_one_student.id,
    ).one()

    assert refreshed_snapshot.id == snapshot_id

    snapshot_count = db.query(
        PublishedReportSnapshot
    ).filter(
        PublishedReportSnapshot.publication_id
        == publication_id,
        PublishedReportSnapshot.student_id
        == school_one_student.id,
    ).count()

    assert snapshot_count == 1

    assert (
        refreshed_snapshot.report_data
        != original_report
    )


# ============================================================
# SNAPSHOT STORES REPORT DATA
# ============================================================


def test_snapshot_preserves_published_report_data(
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
    prepare_complete_result(
        db=db,
        student=school_one_student,
        class_record=school_one_class,
        academic_session=academic_session_one,
        assessment=active_term_assessment,
        score=8,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/result-publications",
        headers=auth_headers(token),
        json=publication_payload(
            class_id=school_one_class.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        ),
    )

    assert response.status_code == 201

    publication_id = response.json()["id"]

    snapshot = db.query(
        PublishedReportSnapshot
    ).filter(
        PublishedReportSnapshot.publication_id
        == publication_id,
        PublishedReportSnapshot.student_id
        == school_one_student.id,
    ).one()

    stored_report = deepcopy(
        snapshot.report_data
    )

    assert stored_report["student"]["student_id"] == (
        school_one_student.id
    )

    assert stored_report["school_info"]["school_id"] == (
        school_admin.school_id
    )

    assert stored_report["term_info"]["term_id"] == (
        first_term.id
    )

    assert (
        stored_report["performance"]["result_status"]
        == "COMPLETE"
    )
