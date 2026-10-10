"""
Security and payment-processing tests for Flutterwave webhooks.
"""


def test_webhook_rejects_missing_authentication(client):
    response = client.post(
        "/api/payments/webhook",
        json={
            "event": "charge.completed",
            "data": {
                "id": 12345,
                "tx_ref": "test-webhook-reference",
            },
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid Flutterwave webhook authentication"
    )


def test_authenticated_webhook_ignores_unknown_transaction(
    client,
    monkeypatch,
):
    from app.api.payments import settings

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 12345,
                "tx_ref": "unknown-test-reference",
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "reason": "Unknown transaction reference",
    }


def test_webhook_does_not_activate_failed_payment(
    client,
    db,
    monkeypatch,
    pending_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="test-failed-webhook-payment",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    def fake_verify_transaction(transaction_id):
        assert str(transaction_id) == "12345"

        return {
            "status": "success",
            "data": {
                "id": 12345,
                "tx_ref": payment.tx_ref,
                "status": "failed",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        fake_verify_transaction,
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 12345,
                "tx_ref": payment.tx_ref,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"

    db.expire_all()
    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert pending_subscription.status == "pending"
    assert pending_subscription.activated_at is None


def test_webhook_activates_verified_successful_payment(
    client,
    db,
    monkeypatch,
    pending_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="test-successful-webhook-payment",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    def fake_verify_transaction(transaction_id):
        assert str(transaction_id) == "67890"

        return {
            "status": "success",
            "data": {
                "id": 67890,
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        fake_verify_transaction,
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 67890,
                "tx_ref": payment.tx_ref,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"

    db.expire_all()
    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "successful"
    assert payment.flutterwave_transaction_id == "67890"
    assert payment.verified_at is not None

    assert pending_subscription.status == "active"
    assert pending_subscription.activated_at is not None

    assert pending_subscription.expires_at is not None
    assert (
        pending_subscription.expires_at
        > pending_subscription.activated_at
    )


def test_duplicate_webhook_does_not_process_payment_twice(
    client,
    db,
    monkeypatch,
    pending_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="test-duplicate-webhook-payment",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    verification_calls = []

    def fake_verify_transaction(transaction_id):
        verification_calls.append(transaction_id)

        return {
            "status": "success",
            "data": {
                "id": 98765,
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        fake_verify_transaction,
    )

    payload = {
        "event": "charge.completed",
        "data": {
            "id": 98765,
            "tx_ref": payment.tx_ref,
        },
    }

    headers = {
        "verif-hash": "test-webhook-secret",
    }

    first_response = client.post(
        "/api/payments/webhook",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "processed"

    db.expire_all()
    db.refresh(payment)
    db.refresh(pending_subscription)

    first_verified_at = payment.verified_at
    first_activated_at = pending_subscription.activated_at

    first_expiration = pending_subscription.expires_at

    assert first_expiration is not None

    second_response = client.post(
        "/api/payments/webhook",
        headers=headers,
        json=payload,
    )

    assert second_response.status_code == 200
    assert second_response.json()["status"] == "already_processed"

    db.expire_all()
    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "successful"
    assert pending_subscription.status == "active"
    assert payment.verified_at == first_verified_at
    assert pending_subscription.activated_at == first_activated_at
    assert pending_subscription.expires_at == first_expiration

    assert len(verification_calls) == 1


def test_webhook_rejects_insufficient_payment_amount(
    client,
    db,
    monkeypatch,
    pending_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="test-insufficient-webhook-payment",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    def fake_verify_transaction(transaction_id):
        return {
            "status": "success",
            "data": {
                "id": 54321,
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "NGN",
                "amount": 10000,
            },
        }

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        fake_verify_transaction,
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 54321,
                "tx_ref": payment.tx_ref,
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Insufficient payment amount"
    )

    db.expire_all()
    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert pending_subscription.status == "pending"
    assert pending_subscription.activated_at is None


def test_webhook_rejects_currency_mismatch(
    client,
    db,
    monkeypatch,
    pending_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="test-currency-mismatch-webhook",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    def fake_verify_transaction(transaction_id):
        assert str(transaction_id) == "65432"

        return {
            "status": "success",
            "data": {
                "id": 65432,
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "USD",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        fake_verify_transaction,
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 65432,
                "tx_ref": payment.tx_ref,
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Payment currency mismatch"
    )

    db.expire_all()
    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert payment.flutterwave_transaction_id is None
    assert pending_subscription.status == "pending"
    assert pending_subscription.activated_at is None


def test_webhook_rejects_transaction_reference_mismatch(
    client,
    db,
    monkeypatch,
    pending_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="expected-webhook-reference",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    def fake_verify_transaction(transaction_id):
        assert str(transaction_id) == "76543"

        return {
            "status": "success",
            "data": {
                "id": 76543,
                "tx_ref": "different-webhook-reference",
                "status": "successful",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        fake_verify_transaction,
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 76543,
                "tx_ref": payment.tx_ref,
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Flutterwave transaction reference mismatch"
    )

    db.expire_all()
    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert payment.flutterwave_transaction_id is None
    assert pending_subscription.status == "pending"
    assert pending_subscription.activated_at is None


# ============================================================
# ADDITIONAL WEBHOOK SECURITY TESTS
# ============================================================


def test_webhook_rejects_invalid_hmac_signature(
    client,
    monkeypatch,
):
    from app.api.payments import settings

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "flutterwave-signature": "invalid-signature",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 12345,
                "tx_ref": "invalid-hmac-reference",
            },
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid Flutterwave webhook authentication"
    )


def test_webhook_rejects_missing_secret_configuration(
    client,
    monkeypatch,
):
    from app.api.payments import settings

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "",
    )

    response = client.post(
        "/api/payments/webhook",
        json={
            "event": "charge.completed",
            "data": {},
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Flutterwave secret hash is not configured"
    )


def test_webhook_rejects_invalid_json(
    client,
    monkeypatch,
):
    from app.api.payments import settings

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
            "Content-Type": "application/json",
        },
        content=b"{invalid-json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid webhook JSON payload"
    )


def test_webhook_ignores_unsupported_event(
    client,
    monkeypatch,
):
    from app.api.payments import settings

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "transfer.completed",
            "data": {
                "id": 12345,
                "tx_ref": "unsupported-event",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert response.json()["reason"] == (
        "Unsupported event"
    )


def test_webhook_ignores_missing_transaction_identifier(
    client,
    monkeypatch,
):
    from app.api.payments import settings

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "tx_ref": "missing-transaction-id",
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "reason": "Missing transaction identifier",
    }


def test_webhook_rejects_transaction_id_mismatch(
    client,
    db,
    monkeypatch,
    pending_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="webhook-id-mismatch",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    def fake_verify_transaction(transaction_id):
        return {
            "status": "success",
            "data": {
                "id": 99999,
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        fake_verify_transaction,
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 12345,
                "tx_ref": payment.tx_ref,
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Flutterwave transaction ID mismatch"
    )

    db.expire_all()
    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert pending_subscription.status == "pending"


def test_webhook_rejects_reused_flutterwave_transaction_id(
    client,
    db,
    monkeypatch,
    pending_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    existing_payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="previous-payment-reference",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="successful",
        payment_provider="flutterwave",
        flutterwave_transaction_id="88888",
    )

    new_payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="new-payment-reference",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add_all([existing_payment, new_payment])
    db.commit()
    db.refresh(new_payment)

    def fake_verify_transaction(transaction_id):
        return {
            "status": "success",
            "data": {
                "id": 88888,
                "tx_ref": new_payment.tx_ref,
                "status": "successful",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        fake_verify_transaction,
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 88888,
                "tx_ref": new_payment.tx_ref,
            },
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Flutterwave transaction has already been used"
    )

    db.expire_all()
    db.refresh(new_payment)
    db.refresh(pending_subscription)

    assert new_payment.status == "pending"
    assert pending_subscription.status == "pending"


def test_webhook_ignores_non_pending_subscription(
    client,
    db,
    monkeypatch,
    cancelled_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    payment = PaymentTransaction(
        school_id=cancelled_subscription.school_id,
        subscription_id=cancelled_subscription.id,
        tx_ref="cancelled-subscription-payment",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    def unexpected_verification(transaction_id):
        raise AssertionError(
            "Cancelled subscription must not be verified"
        )

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        unexpected_verification,
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 12345,
                "tx_ref": payment.tx_ref,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"

    db.expire_all()
    db.refresh(payment)
    db.refresh(cancelled_subscription)

    assert payment.status == "pending"
    assert cancelled_subscription.status == "cancelled"


def test_webhook_handles_flutterwave_verification_failure(
    client,
    db,
    monkeypatch,
    pending_subscription,
):
    from decimal import Decimal

    from app.api.payments import settings
    from app.models.payment_transaction import PaymentTransaction
    from app.services.flutterwave_service import FlutterwaveServiceError

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    payment = PaymentTransaction(
        school_id=pending_subscription.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="verification-service-failure",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    def fake_verify_transaction(transaction_id):
        raise FlutterwaveServiceError(
            "Simulated verification failure"
        )

    monkeypatch.setattr(
        "app.api.payments.verify_transaction",
        fake_verify_transaction,
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
            "data": {
                "id": 12345,
                "tx_ref": payment.tx_ref,
            },
        },
    )

    assert response.status_code == 502

    db.expire_all()
    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert pending_subscription.status == "pending"


def test_webhook_ignores_missing_data(
    client,
    monkeypatch,
):
    from app.api.payments import settings

    monkeypatch.setattr(
        settings,
        "flutterwave_secret_hash",
        "test-webhook-secret",
    )

    response = client.post(
        "/api/payments/webhook",
        headers={
            "verif-hash": "test-webhook-secret",
        },
        json={
            "event": "charge.completed",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ignored",
        "reason": "Missing webhook data",
    }
