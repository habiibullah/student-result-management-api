from decimal import Decimal

from app.models.payment_transaction import PaymentTransaction


def test_callback_rejects_missing_reference(client):
    response = client.get(
        "/api/payments/callback"
    )

    assert response.status_code == 200
    assert "Payment reference is missing" in response.text


def test_callback_rejects_unknown_reference(client):
    response = client.get(
        "/api/payments/callback",
        params={
            "status": "successful",
            "tx_ref": "UNKNOWN-REFERENCE",
            "transaction_id": "123456",
        },
    )

    assert response.status_code == 200
    assert "not recognized" in response.text


def test_cancelled_checkout_does_not_activate_subscription(
    client,
    db,
    pending_subscription,
    school_admin,
):
    payment = PaymentTransaction(
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="TEST-CANCELLED-CHECKOUT",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()

    response = client.get(
        "/api/payments/callback",
        params={
            "status": "cancelled",
            "tx_ref": payment.tx_ref,
            "transaction_id": "123456",
        },
    )

    db.refresh(payment)
    db.refresh(pending_subscription)

    assert response.status_code == 200
    assert "not completed successfully" in response.text

    assert payment.status == "pending"
    assert pending_subscription.status == "pending"

def test_successful_callback_activates_subscription(
    client,
    db,
    monkeypatch,
    pending_subscription,
    school_admin,
):
    payment = PaymentTransaction(
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="TEST-SUCCESSFUL-CALLBACK",
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
                "id": int(transaction_id),
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        fake_verify_transaction,
    )

    response = client.get(
        "/api/payments/callback",
        params={
            "status": "successful",
            "tx_ref": payment.tx_ref,
            "transaction_id": "123456",
        },
    )

    db.refresh(payment)
    db.refresh(pending_subscription)

    assert response.status_code == 200
    assert "Payment verified successfully" in response.text

    assert payment.status == "successful"
    assert payment.flutterwave_transaction_id == "123456"
    assert payment.verified_at is not None

    assert pending_subscription.status == "active"
    assert pending_subscription.activated_at is not None

def test_callback_rejects_underpayment(
    client,
    db,
    monkeypatch,
    pending_subscription,
    school_admin,
):
    payment = PaymentTransaction(
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="TEST-UNDERPAYMENT-CALLBACK",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()

    def fake_verify_transaction(transaction_id):
        return {
            "status": "success",
            "data": {
                "id": int(transaction_id),
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "NGN",
                "amount": 10000,
            },
        }

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        fake_verify_transaction,
    )

    response = client.get(
        "/api/payments/callback",
        params={
            "status": "successful",
            "tx_ref": payment.tx_ref,
            "transaction_id": "234567",
        },
    )

    db.refresh(payment)
    db.refresh(pending_subscription)

    assert response.status_code == 200
    assert "verification could not be completed" in response.text
    assert payment.status == "pending"
    assert pending_subscription.status == "pending"


def test_repeated_successful_callback_is_idempotent(
    client,
    db,
    monkeypatch,
    pending_subscription,
    school_admin,
):
    payment = PaymentTransaction(
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="TEST-REPEATED-CALLBACK",
        amount=Decimal("20000.00"),
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.commit()

    verification_calls = 0

    def fake_verify_transaction(transaction_id):
        nonlocal verification_calls
        verification_calls += 1

        return {
            "status": "success",
            "data": {
                "id": int(transaction_id),
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        fake_verify_transaction,
    )

    params = {
        "status": "successful",
        "tx_ref": payment.tx_ref,
        "transaction_id": "345678",
    }

    first_response = client.get(
        "/api/payments/callback",
        params=params,
    )

    db.refresh(payment)
    first_verified_at = payment.verified_at

    second_response = client.get(
        "/api/payments/callback",
        params=params,
    )

    db.refresh(payment)
    db.refresh(pending_subscription)

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert "Payment verified successfully" in first_response.text
    assert "Payment verified successfully" in second_response.text

    assert payment.status == "successful"
    assert pending_subscription.status == "active"
    assert payment.verified_at == first_verified_at

    assert verification_calls == 1