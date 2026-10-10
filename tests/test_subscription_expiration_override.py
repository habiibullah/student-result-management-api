import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.subscription_expiration_override import (
    SubscriptionExpirationOverride,
)


def login(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_platform_admin_can_override_expiration(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)

    original_expiration = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=30)
    )

    active_subscription.expires_at = original_expiration
    db.commit()

    new_expiration = (
        datetime.now(timezone.utc)
        + timedelta(days=60)
    ).replace(microsecond=0)

    reason = (
        "Exceptional extension approved "
        "by the platform administrator"
    )

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "expires_at": new_expiration.isoformat(),
            "reason": reason,
        },
    )

    assert response.status_code == 200, response.text

    db.refresh(active_subscription)

    expected_expiration = new_expiration.replace(
        tzinfo=None
    )

    assert active_subscription.expires_at == expected_expiration

    audit_record = db.scalar(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    )

    assert audit_record is not None
    assert audit_record.admin_user_id == platform_admin.id
    assert audit_record.previous_expires_at == original_expiration
    assert audit_record.new_expires_at == expected_expiration
    assert audit_record.reason == reason



def test_school_admin_cannot_override_expiration(
    client,
    db,
    school_admin,
    active_subscription,
):
    original_expiration = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=30)
    )

    active_subscription.expires_at = original_expiration
    db.commit()

    token = login(client, school_admin.email)

    new_expiration = (
        datetime.now(timezone.utc)
        + timedelta(days=60)
    )

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "expires_at": new_expiration.isoformat(),
            "reason": "Unauthorized school administrator extension",
        },
    )

    assert response.status_code == 403

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original_expiration

    audit_records = db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    ).all()

    assert audit_records == []



import pytest


def override_request(
    client,
    subscription_id,
    token,
    expires_at,
    reason="Exceptional administrative subscription adjustment",
):
    return client.patch(
        f"/api/subscriptions/{subscription_id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": expires_at,
            "reason": reason,
        },
    )


def audit_records_for(db, subscription_id):
    return list(
        db.scalars(
            select(SubscriptionExpirationOverride).where(
                SubscriptionExpirationOverride.subscription_id
                == subscription_id
            )
        ).all()
    )


def test_unauthenticated_user_cannot_override_expiration(
    client,
    active_subscription,
):
    future = datetime.now(timezone.utc) + timedelta(days=30)

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        json={
            "expires_at": future.isoformat(),
            "reason": "Unauthorized subscription extension attempt",
        },
    )

    assert response.status_code in (401, 403)


def test_platform_admin_cannot_set_past_expiration(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)
    original = active_subscription.expires_at

    past = datetime.now(timezone.utc) - timedelta(days=1)

    response = override_request(
        client,
        active_subscription.id,
        token,
        past.isoformat(),
    )

    assert response.status_code == 422

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original
    assert audit_records_for(db, active_subscription.id) == []


def test_platform_admin_cannot_set_current_expiration(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)
    original = active_subscription.expires_at

    response = override_request(
        client,
        active_subscription.id,
        token,
        datetime.now(timezone.utc).isoformat(),
    )

    assert response.status_code == 422

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original
    assert audit_records_for(db, active_subscription.id) == []


def test_expiration_override_requires_timezone(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)
    original = active_subscription.expires_at

    naive_future = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=30)
    )

    response = override_request(
        client,
        active_subscription.id,
        token,
        naive_future.isoformat(),
    )

    assert response.status_code == 422

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original
    assert audit_records_for(db, active_subscription.id) == []


@pytest.mark.parametrize(
    "reason",
    [
        "",
        "short",
        "          ",
        "   short   ",
    ],
)
def test_expiration_override_rejects_invalid_reason(
    client,
    db,
    platform_admin,
    active_subscription,
    reason,
):
    token = login(client, platform_admin.email)
    original = active_subscription.expires_at
    future = datetime.now(timezone.utc) + timedelta(days=30)

    response = override_request(
        client,
        active_subscription.id,
        token,
        future.isoformat(),
        reason=reason,
    )

    assert response.status_code == 422

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original
    assert audit_records_for(db, active_subscription.id) == []


def test_expiration_override_rejects_missing_reason(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)
    original = active_subscription.expires_at
    future = datetime.now(timezone.utc) + timedelta(days=30)

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={"expires_at": future.isoformat()},
    )

    assert response.status_code == 422

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original
    assert audit_records_for(db, active_subscription.id) == []


def test_expiration_override_rejects_reason_over_500_characters(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)
    future = datetime.now(timezone.utc) + timedelta(days=30)

    response = override_request(
        client,
        active_subscription.id,
        token,
        future.isoformat(),
        reason="A" * 501,
    )

    assert response.status_code == 422
    assert audit_records_for(db, active_subscription.id) == []


@pytest.mark.parametrize(
    "fixture_name",
    [
        "pending_subscription",
        "cancelled_subscription",
        "expired_subscription",
    ],
)
def test_cannot_override_inactive_subscription(
    client,
    db,
    platform_admin,
    fixture_name,
    request,
):
    subscription = request.getfixturevalue(fixture_name)
    token = login(client, platform_admin.email)
    original = subscription.expires_at
    original_status = subscription.status

    future = datetime.now(timezone.utc) + timedelta(days=30)

    response = override_request(
        client,
        subscription.id,
        token,
        future.isoformat(),
    )

    assert response.status_code == 409

    db.refresh(subscription)
    assert subscription.status == original_status
    assert subscription.expires_at == original
    assert audit_records_for(db, subscription.id) == []


def test_cannot_override_nonexistent_subscription(
    client,
    db,
    platform_admin,
):
    token = login(client, platform_admin.email)
    future = datetime.now(timezone.utc) + timedelta(days=30)

    response = override_request(
        client,
        999999,
        token,
        future.isoformat(),
    )

    assert response.status_code == 404
    assert db.query(SubscriptionExpirationOverride).count() == 0


def test_cannot_override_with_same_expiration(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)

    expiration = (
        datetime.now(timezone.utc)
        + timedelta(days=30)
    ).replace(microsecond=0)

    active_subscription.expires_at = expiration.replace(tzinfo=None)
    db.commit()

    response = override_request(
        client,
        active_subscription.id,
        token,
        expiration.isoformat(),
    )

    assert response.status_code == 409

    db.refresh(active_subscription)
    assert active_subscription.expires_at == expiration.replace(
        tzinfo=None
    )
    assert audit_records_for(db, active_subscription.id) == []


def test_can_override_legacy_subscription_without_expiration(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)

    assert active_subscription.expires_at is None

    future = (
        datetime.now(timezone.utc)
        + timedelta(days=45)
    ).replace(microsecond=0)

    response = override_request(
        client,
        active_subscription.id,
        token,
        future.isoformat(),
        reason="Legacy subscription requires an approved expiration",
    )

    assert response.status_code == 200, response.text

    db.refresh(active_subscription)
    assert active_subscription.expires_at == future.replace(tzinfo=None)

    records = audit_records_for(db, active_subscription.id)

    assert len(records) == 1
    assert records[0].admin_user_id == platform_admin.id
    assert records[0].previous_expires_at is None
    assert records[0].new_expires_at == future.replace(tzinfo=None)


def test_multiple_overrides_preserve_complete_audit_history(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)

    first_expiration = (
        datetime.now(timezone.utc)
        + timedelta(days=30)
    ).replace(microsecond=0)

    second_expiration = (
        datetime.now(timezone.utc)
        + timedelta(days=60)
    ).replace(microsecond=0)

    first_response = override_request(
        client,
        active_subscription.id,
        token,
        first_expiration.isoformat(),
        reason="First exceptional administrative adjustment",
    )

    assert first_response.status_code == 200, first_response.text

    second_response = override_request(
        client,
        active_subscription.id,
        token,
        second_expiration.isoformat(),
        reason="Second exceptional administrative adjustment",
    )

    assert second_response.status_code == 200, second_response.text

    db.refresh(active_subscription)

    assert active_subscription.expires_at == second_expiration.replace(
        tzinfo=None
    )

    records = sorted(
        audit_records_for(db, active_subscription.id),
        key=lambda record: record.id,
    )

    assert len(records) == 2

    assert records[0].previous_expires_at is None
    assert records[0].new_expires_at == first_expiration.replace(
        tzinfo=None
    )

    assert records[1].previous_expires_at == first_expiration.replace(
        tzinfo=None
    )
    assert records[1].new_expires_at == second_expiration.replace(
        tzinfo=None
    )

    assert all(
        record.admin_user_id == platform_admin.id
        for record in records
    )

    assert all(record.created_at is not None for record in records)


def test_timezone_offset_is_normalized_to_utc(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)

    future_utc = (
        datetime.now(timezone.utc)
        + timedelta(days=30)
    ).replace(microsecond=0)

    from datetime import timedelta as td
    local_timezone = timezone(td(hours=1))

    local_expiration = future_utc.astimezone(local_timezone)

    response = override_request(
        client,
        active_subscription.id,
        token,
        local_expiration.isoformat(),
    )

    assert response.status_code == 200, response.text

    db.refresh(active_subscription)

    assert active_subscription.expires_at == future_utc.replace(
        tzinfo=None
    )



# ============================================================
# ADDITIONAL EXPIRATION OVERRIDE SECURITY TESTS
# ============================================================


def test_unauthenticated_user_cannot_override_expiration(
    client,
    db,
    active_subscription,
):
    original_expiration = active_subscription.expires_at

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        json={
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(days=60)
            ).isoformat(),
            "reason": "Unauthorized expiration adjustment attempt",
        },
    )

    assert response.status_code in (401, 403)

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original_expiration

    assert db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    ).all() == []


def test_past_expiration_date_is_rejected(
    client,
    db,
    platform_admin,
    active_subscription,
):
    original_expiration = active_subscription.expires_at
    token = login(client, platform_admin.email)

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": (
                datetime.now(timezone.utc)
                - timedelta(days=1)
            ).isoformat(),
            "reason": "Attempt to assign an expired date",
        },
    )

    assert response.status_code == 422

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original_expiration

    assert db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    ).all() == []


def test_expiration_without_timezone_is_rejected(
    client,
    db,
    platform_admin,
    active_subscription,
):
    original_expiration = active_subscription.expires_at
    token = login(client, platform_admin.email)

    naive_expiration = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=60)
    )

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": naive_expiration.isoformat(),
            "reason": "Attempt with an ambiguous timezone",
        },
    )

    assert response.status_code == 422

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original_expiration

    assert db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    ).all() == []


def test_short_reason_is_rejected(
    client,
    db,
    platform_admin,
    active_subscription,
):
    original_expiration = active_subscription.expires_at
    token = login(client, platform_admin.email)

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(days=60)
            ).isoformat(),
            "reason": "Short",
        },
    )

    assert response.status_code == 422

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original_expiration

    assert db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    ).all() == []


def test_whitespace_only_reason_is_rejected(
    client,
    db,
    platform_admin,
    active_subscription,
):
    original_expiration = active_subscription.expires_at
    token = login(client, platform_admin.email)

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(days=60)
            ).isoformat(),
            "reason": "               ",
        },
    )

    assert response.status_code == 422

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original_expiration

    assert db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    ).all() == []


def test_pending_subscription_cannot_be_overridden(
    client,
    db,
    platform_admin,
    pending_subscription,
):
    original_expiration = pending_subscription.expires_at
    token = login(client, platform_admin.email)

    response = client.patch(
        f"/api/subscriptions/{pending_subscription.id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(days=60)
            ).isoformat(),
            "reason": "Attempt to extend pending subscription",
        },
    )

    assert response.status_code == 409

    db.refresh(pending_subscription)
    assert pending_subscription.status == "pending"
    assert pending_subscription.expires_at == original_expiration

    assert db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == pending_subscription.id
        )
    ).all() == []


def test_expired_subscription_cannot_be_overridden(
    client,
    db,
    platform_admin,
    expired_subscription,
):
    original_expiration = expired_subscription.expires_at
    token = login(client, platform_admin.email)

    response = client.patch(
        f"/api/subscriptions/{expired_subscription.id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(days=60)
            ).isoformat(),
            "reason": "Attempt to extend expired subscription",
        },
    )

    assert response.status_code == 409

    db.refresh(expired_subscription)
    assert expired_subscription.status == "expired"
    assert expired_subscription.expires_at == original_expiration

    assert db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == expired_subscription.id
        )
    ).all() == []


def test_nonexistent_subscription_returns_404(
    client,
    db,
    platform_admin,
):
    token = login(client, platform_admin.email)

    response = client.patch(
        "/api/subscriptions/999999/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": (
                datetime.now(timezone.utc)
                + timedelta(days=60)
            ).isoformat(),
            "reason": "Attempt to update nonexistent subscription",
        },
    )

    assert response.status_code == 404

    assert db.scalars(
        select(SubscriptionExpirationOverride)
    ).all() == []


def test_same_expiration_date_is_rejected(
    client,
    db,
    platform_admin,
    active_subscription,
):
    original_expiration = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=60)
    ).replace(microsecond=0)

    active_subscription.expires_at = original_expiration
    db.commit()

    token = login(client, platform_admin.email)

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": original_expiration.replace(
                tzinfo=timezone.utc
            ).isoformat(),
            "reason": "Attempt to repeat existing expiration date",
        },
    )

    assert response.status_code == 409

    db.refresh(active_subscription)
    assert active_subscription.expires_at == original_expiration

    assert db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    ).all() == []


def test_legacy_subscription_without_expiration_can_be_adjusted(
    client,
    db,
    platform_admin,
    active_subscription,
):
    active_subscription.expires_at = None
    db.commit()

    token = login(client, platform_admin.email)

    new_expiration = (
        datetime.now(timezone.utc)
        + timedelta(days=90)
    ).replace(microsecond=0)

    response = client.patch(
        f"/api/subscriptions/{active_subscription.id}/expiration",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": new_expiration.isoformat(),
            "reason": "Set expiration for legacy paid subscription",
        },
    )

    assert response.status_code == 200, response.text

    db.refresh(active_subscription)

    assert active_subscription.expires_at == (
        new_expiration.replace(tzinfo=None)
    )

    audit_record = db.scalar(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    )

    assert audit_record is not None
    assert audit_record.previous_expires_at is None
    assert audit_record.admin_user_id == platform_admin.id


def test_multiple_overrides_preserve_audit_history(
    client,
    db,
    platform_admin,
    active_subscription,
):
    token = login(client, platform_admin.email)

    first_expiration = (
        datetime.now(timezone.utc)
        + timedelta(days=60)
    ).replace(microsecond=0)

    second_expiration = (
        datetime.now(timezone.utc)
        + timedelta(days=90)
    ).replace(microsecond=0)

    url = (
        f"/api/subscriptions/{active_subscription.id}/expiration"
    )

    first_response = client.patch(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": first_expiration.isoformat(),
            "reason": "First exceptional administrative extension",
        },
    )

    assert first_response.status_code == 200, first_response.text

    second_response = client.patch(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={
            "expires_at": second_expiration.isoformat(),
            "reason": "Second exceptional administrative extension",
        },
    )

    assert second_response.status_code == 200, second_response.text

    db.refresh(active_subscription)

    assert active_subscription.expires_at == (
        second_expiration.replace(tzinfo=None)
    )

    records = db.scalars(
        select(SubscriptionExpirationOverride)
        .where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
        .order_by(SubscriptionExpirationOverride.id)
    ).all()

    assert len(records) == 2

    assert records[0].new_expires_at == (
        first_expiration.replace(tzinfo=None)
    )

    assert records[1].previous_expires_at == (
        first_expiration.replace(tzinfo=None)
    )

    assert records[1].new_expires_at == (
        second_expiration.replace(tzinfo=None)
    )



def test_failed_audit_insert_rolls_back_expiration(
    client,
    db,
    platform_admin,
    active_subscription,
    monkeypatch,
):
    from sqlalchemy.orm import Session

    original_expiration = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=30)
    )

    active_subscription.expires_at = original_expiration
    db.commit()

    token = login(client, platform_admin.email)

    new_expiration = (
        datetime.now(timezone.utc)
        + timedelta(days=60)
    ).isoformat()

    original_flush = Session.flush

    def fail_audit_flush(self, objects=None):
        if any(
            isinstance(obj, SubscriptionExpirationOverride)
            for obj in self.new
        ):
            raise RuntimeError("Simulated audit insertion failure")

        return original_flush(self, objects)

    monkeypatch.setattr(Session, "flush", fail_audit_flush)

    with pytest.raises(RuntimeError, match="Simulated audit insertion failure"):
        client.patch(
            f"/api/subscriptions/{active_subscription.id}/expiration",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "expires_at": new_expiration,
                "reason": "Test atomic database transaction rollback",
            },
        )

    # Close the failed transaction before reading again.
    db.rollback()

    db.refresh(active_subscription)

    assert active_subscription.expires_at == original_expiration

    records = db.scalars(
        select(SubscriptionExpirationOverride).where(
            SubscriptionExpirationOverride.subscription_id
            == active_subscription.id
        )
    ).all()

    assert records == []
