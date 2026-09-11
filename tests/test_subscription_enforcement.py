import pytest
from fastapi import HTTPException

from app.services.subscription_service import (
    require_active_term_subscription,
)


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


def assert_subscription_required(exc_info):
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "An active subscription is required "
        "for this academic term"
    )


# ============================================================
# SUBSCRIPTION SERVICE
# ============================================================


def test_active_term_subscription_is_accepted(
    db,
    school_one,
    academic_session_one,
    first_term,
    active_subscription,
):
    subscription = require_active_term_subscription(
        db=db,
        school_id=school_one.id,
        academic_session_id=academic_session_one.id,
        term_id=first_term.id,
    )

    assert subscription.id == active_subscription.id
    assert subscription.status == "active"


def test_pending_subscription_is_rejected(
    db,
    school_one,
    academic_session_one,
    second_term,
    pending_subscription,
):
    with pytest.raises(HTTPException) as exc_info:
        require_active_term_subscription(
            db=db,
            school_id=school_one.id,
            academic_session_id=academic_session_one.id,
            term_id=second_term.id,
        )

    assert_subscription_required(exc_info)


def test_cancelled_subscription_is_rejected(
    db,
    school_one,
    academic_session_one,
    third_term,
    cancelled_subscription,
):
    with pytest.raises(HTTPException) as exc_info:
        require_active_term_subscription(
            db=db,
            school_id=school_one.id,
            academic_session_id=academic_session_one.id,
            term_id=third_term.id,
        )

    assert_subscription_required(exc_info)


def test_expired_subscription_is_rejected(
    db,
    school_one,
    academic_session_one,
    test_extra_term,
    expired_subscription,
):
    with pytest.raises(HTTPException) as exc_info:
        require_active_term_subscription(
            db=db,
            school_id=school_one.id,
            academic_session_id=academic_session_one.id,
            term_id=test_extra_term.id,
        )

    assert_subscription_required(exc_info)


def test_missing_subscription_is_rejected(
    db,
    school_one,
    academic_session_one,
):
    with pytest.raises(HTTPException) as exc_info:
        require_active_term_subscription(
            db=db,
            school_id=school_one.id,
            academic_session_id=academic_session_one.id,
            term_id=999999,
        )

    assert_subscription_required(exc_info)


def test_subscription_from_another_school_cannot_unlock_term(
    db,
    school_two,
    academic_session_one,
    first_term,
    active_subscription,
):
    with pytest.raises(HTTPException) as exc_info:
        require_active_term_subscription(
            db=db,
            school_id=school_two.id,
            academic_session_id=academic_session_one.id,
            term_id=first_term.id,
        )

    assert_subscription_required(exc_info)


def test_subscription_requires_exact_academic_session(
    db,
    school_one,
    academic_session_two,
    first_term,
    active_subscription,
):
    with pytest.raises(HTTPException) as exc_info:
        require_active_term_subscription(
            db=db,
            school_id=school_one.id,
            academic_session_id=academic_session_two.id,
            term_id=first_term.id,
        )

    assert_subscription_required(exc_info)


# ============================================================
# SCHOOL SUBSCRIPTION ACCESS
# ============================================================


def test_school_admin_can_list_own_subscriptions(
    client,
    school_admin,
    active_subscription,
    pending_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/subscriptions/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        subscription["id"]
        for subscription in data
    }

    assert active_subscription.id in returned_ids
    assert pending_subscription.id in returned_ids


def test_school_admin_cannot_read_other_school_subscription(
    client,
    school_admin,
    school_two_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        (
            "/api/subscriptions/me/"
            f"{school_two_subscription.id}"
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Subscription not found"
    )


def test_school_admin_cannot_list_all_subscriptions(
    client,
    school_admin,
    active_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/subscriptions",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_platform_admin_can_list_all_subscriptions(
    client,
    platform_admin,
    active_subscription,
    school_two_subscription,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.get(
        "/api/subscriptions",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    returned_ids = {
        subscription["id"]
        for subscription in data
    }

    assert active_subscription.id in returned_ids
    assert school_two_subscription.id in returned_ids


# ============================================================
# SUBSCRIPTION STATUS MANAGEMENT
# ============================================================


def test_school_admin_cannot_activate_subscription(
    client,
    school_admin,
    pending_subscription,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.patch(
        (
            "/api/subscriptions/"
            f"{pending_subscription.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "status": "active",
        },
    )

    assert response.status_code == 403


def test_platform_admin_can_activate_pending_subscription(
    client,
    platform_admin,
    pending_subscription,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        (
            "/api/subscriptions/"
            f"{pending_subscription.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "status": "active",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "active"
    assert data["activated_at"] is not None


def test_subscription_status_update_is_idempotent(
    client,
    platform_admin,
    active_subscription,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        (
            "/api/subscriptions/"
            f"{active_subscription.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "status": "active",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_invalid_pending_to_expired_transition_is_blocked(
    client,
    platform_admin,
    pending_subscription,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        (
            "/api/subscriptions/"
            f"{pending_subscription.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "status": "expired",
        },
    )

    assert response.status_code == 409


def test_expired_subscription_cannot_be_reactivated(
    client,
    platform_admin,
    expired_subscription,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        (
            "/api/subscriptions/"
            f"{expired_subscription.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "status": "active",
        },
    )

    assert response.status_code == 409


def test_cancelled_subscription_can_return_to_pending(
    client,
    platform_admin,
    cancelled_subscription,
):
    token = login(
        client,
        platform_admin.email,
    )

    response = client.patch(
        (
            "/api/subscriptions/"
            f"{cancelled_subscription.id}/status"
        ),
        headers=auth_headers(token),
        json={
            "status": "pending",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


# ============================================================
# SUBSCRIPTION CREATION
# ============================================================


def test_duplicate_term_subscription_is_rejected(
    client,
    school_admin,
    active_subscription,
    basic_subscription_plan,
    academic_session_one,
    first_term,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/subscriptions",
        headers=auth_headers(token),
        json={
            "subscription_plan_id": (
                basic_subscription_plan.id
            ),
            "academic_session_id": (
                academic_session_one.id
            ),
            "term_id": first_term.id,
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "A subscription already exists for "
        "this school, academic session, and term"
    )


def test_new_subscription_starts_as_pending(
    client,
    school_admin,
    basic_subscription_plan,
    academic_session_one,
    first_term,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/subscriptions",
        headers=auth_headers(token),
        json={
            "subscription_plan_id": (
                basic_subscription_plan.id
            ),
            "academic_session_id": (
                academic_session_one.id
            ),
            "term_id": first_term.id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "pending"
    assert data["school_id"] == school_admin.school_id
    assert data["academic_session_id"] == (
        academic_session_one.id
    )
    assert data["term_id"] == first_term.id


def test_school_cannot_subscribe_to_another_schools_session(
    client,
    school_admin,
    basic_subscription_plan,
    academic_session_two,
    school_two_term,
):
    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/subscriptions",
        headers=auth_headers(token),
        json={
            "subscription_plan_id": (
                basic_subscription_plan.id
            ),
            "academic_session_id": (
                academic_session_two.id
            ),
            "term_id": school_two_term.id,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Academic session not found"
    )
