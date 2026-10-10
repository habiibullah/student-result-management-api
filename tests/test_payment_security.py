from decimal import Decimal

from app.models.payment_transaction import PaymentTransaction


# ============================================================
# AUTH HELPERS
# ============================================================


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


# ============================================================
# DATABASE HELPERS
# ============================================================


def create_payment(
    db,
    school_id,
    subscription_id,
    tx_ref,
    amount=Decimal("20000.00"),
    currency="NGN",
    payment_status="pending",
    payment_link=None,
    flutterwave_transaction_id=None,
):
    payment = PaymentTransaction(
        school_id=school_id,
        subscription_id=subscription_id,
        tx_ref=tx_ref,
        amount=amount,
        currency=currency,
        status=payment_status,
        payment_provider="flutterwave",
        payment_link=payment_link,
        flutterwave_transaction_id=(
            flutterwave_transaction_id
        ),
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


# ============================================================
# INITIALIZATION
# ============================================================


def test_school_admin_can_initialize_own_pending_subscription(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    def fake_initialize_payment(
        tx_ref,
        amount,
        currency,
        customer_email,
        customer_name,
        customer_phone,
        subscription_id,
    ):
        return {
            "status": "success",
            "data": {
                "link": "https://checkout.test/payment",
            },
        }

    monkeypatch.setattr(
        "app.api.payments.initialize_payment",
        fake_initialize_payment,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/payments/initialize",
        headers=auth_headers(token),
        json={
            "subscription_id": pending_subscription.id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["subscription_id"] == (
        pending_subscription.id
    )

    assert data["status"] == "pending"
    assert data["currency"] == "NGN"

    assert data["payment_link"] == (
        "https://checkout.test/payment"
    )

    assert data["tx_ref"].startswith(
        f"SRMS-S{school_admin.school_id}-"
        f"SUB{pending_subscription.id}-"
    )

    payment = db.query(
        PaymentTransaction
    ).filter(
        PaymentTransaction.id == data["payment_id"]
    ).one()

    assert payment.school_id == school_admin.school_id
    assert payment.subscription_id == (
        pending_subscription.id
    )
    assert payment.status == "pending"


def test_existing_pending_payment_link_is_reused(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="TEST-PENDING-REUSE",
        payment_link=(
            "https://checkout.test/existing-payment"
        ),
    )

    def provider_should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "Flutterwave initialization should not be called"
        )

    monkeypatch.setattr(
        "app.api.payments.initialize_payment",
        provider_should_not_be_called,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/payments/initialize",
        headers=auth_headers(token),
        json={
            "subscription_id": pending_subscription.id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == payment.id
    assert data["tx_ref"] == payment.tx_ref
    assert data["payment_link"] == (
        payment.payment_link
    )


def test_retry_reuses_existing_pending_checkout(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    old_payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="TEST-OLD-CHECKOUT",
        payment_link="https://checkout.test/old",
    )

    def provider_should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "Retry must not create another checkout"
        )

    monkeypatch.setattr(
        "app.api.payments.initialize_payment",
        provider_should_not_be_called,
    )

    token = login(client, school_admin.email)

    response = client.post(
        "/api/payments/initialize",
        headers=auth_headers(token),
        json={
            "subscription_id": pending_subscription.id,
            "retry": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == old_payment.id
    assert data["tx_ref"] == old_payment.tx_ref
    assert data["payment_link"] == old_payment.payment_link

    payments = (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.subscription_id
            == pending_subscription.id
        )
        .all()
    )

    assert len(payments) == 1


def test_active_subscription_cannot_initialize_payment(
    client,
    monkeypatch,
    school_admin,
    active_subscription,
):
    def provider_should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "Flutterwave initialization should not be called"
        )

    monkeypatch.setattr(
        "app.api.payments.initialize_payment",
        provider_should_not_be_called,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/payments/initialize",
        headers=auth_headers(token),
        json={
            "subscription_id": active_subscription.id,
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Payment can only be initialized for "
        "a pending subscription"
    )


def test_school_admin_cannot_initialize_other_school_subscription(
    client,
    monkeypatch,
    school_admin,
    school_two_subscription,
):
    def provider_should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "Flutterwave initialization should not be called"
        )

    monkeypatch.setattr(
        "app.api.payments.initialize_payment",
        provider_should_not_be_called,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        "/api/payments/initialize",
        headers=auth_headers(token),
        json={
            "subscription_id": (
                school_two_subscription.id
            ),
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Subscription not found"
    )


# ============================================================
# PAYMENT LIST / READ TENANT ISOLATION
# ============================================================


def test_payment_list_contains_only_own_school(
    client,
    db,
    school_admin,
    other_school_admin,
    pending_subscription,
    school_two_subscription,
):
    own_payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="OWN-SCHOOL-PAYMENT",
    )

    other_payment = create_payment(
        db=db,
        school_id=other_school_admin.school_id,
        subscription_id=school_two_subscription.id,
        tx_ref="OTHER-SCHOOL-PAYMENT",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        "/api/payments",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    returned_ids = {
        payment["id"]
        for payment in response.json()
    }

    assert own_payment.id in returned_ids
    assert other_payment.id not in returned_ids


def test_school_admin_can_read_own_payment(
    client,
    db,
    school_admin,
    pending_subscription,
):
    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="OWN-PAYMENT-READ",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/payments/{payment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == payment.id
    assert response.json()["school_id"] == (
        school_admin.school_id
    )


def test_school_admin_cannot_read_other_school_payment(
    client,
    db,
    school_admin,
    other_school_admin,
    school_two_subscription,
):
    payment = create_payment(
        db=db,
        school_id=other_school_admin.school_id,
        subscription_id=school_two_subscription.id,
        tx_ref="OTHER-PAYMENT-READ",
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.get(
        f"/api/payments/{payment.id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Payment transaction not found"
    )


# ============================================================
# MANUAL VERIFICATION
# ============================================================


def test_successful_verification_activates_subscription(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="VERIFY-SUCCESS-001",
    )

    transaction_id = "900001"

    def fake_verify_transaction(received_transaction_id):
        assert str(received_transaction_id) == (
            transaction_id
        )

        return {
            "status": "success",
            "data": {
                "id": transaction_id,
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

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": transaction_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == payment.id
    assert data["subscription_id"] == (
        pending_subscription.id
    )
    assert data["payment_status"] == "successful"
    assert data["subscription_status"] == "active"
    assert data["flutterwave_transaction_id"] == (
        transaction_id
    )
    assert data["verified_at"] is not None

    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "successful"
    assert payment.flutterwave_transaction_id == (
        transaction_id
    )
    assert payment.verified_at is not None

    assert pending_subscription.status == "active"
    assert pending_subscription.activated_at is not None


    from app.services.subscription_expiration import (
        calculate_subscription_expiration,
    )
    from app.models.term import Term

    term = db.get(Term, pending_subscription.term_id)

    expected_expiration = calculate_subscription_expiration(
        term.closing_date,
        activated_at=pending_subscription.activated_at,
    )

    assert pending_subscription.expires_at == expected_expiration

def test_verification_is_idempotent_for_same_transaction(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="VERIFY-IDEMPOTENT-001",
    )

    transaction_id = "900002"

    def fake_verify_transaction(received_transaction_id):
        return {
            "status": "success",
            "data": {
                "id": transaction_id,
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

    token = login(
        client,
        school_admin.email,
    )

    first_response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": transaction_id,
        },
    )

    assert first_response.status_code == 200

    db.refresh(pending_subscription)

    first_expiration = pending_subscription.expires_at

    assert first_expiration is not None

    first_verified_at = first_response.json()[
        "verified_at"
    ]

    def provider_should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "Provider verification should not be called "
            "for an already verified payment"
        )

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        provider_should_not_be_called,
    )

    second_response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": transaction_id,
        },
    )

    assert second_response.status_code == 200

    second_data = second_response.json()

    assert second_data["payment_status"] == (
        "successful"
    )
    assert second_data["subscription_status"] == (
        "active"
    )
    assert second_data["flutterwave_transaction_id"] == (
        transaction_id
    )
    assert second_data["verified_at"] == first_verified_at
    db.refresh(pending_subscription)

    assert pending_subscription.expires_at == first_expiration


def test_verified_payment_rejects_different_transaction_id(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="VERIFY-DIFFERENT-ID",
    )

    original_transaction_id = "900003"

    def fake_verify_transaction(received_transaction_id):
        return {
            "status": "success",
            "data": {
                "id": original_transaction_id,
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

    token = login(
        client,
        school_admin.email,
    )

    first_response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": original_transaction_id,
        },
    )

    assert first_response.status_code == 200

    def provider_should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "Provider verification should not be called"
        )

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        provider_should_not_be_called,
    )

    second_response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": "999999",
        },
    )

    assert second_response.status_code == 409

    assert second_response.json()["detail"] == (
        "Payment has already been verified "
        "with another transaction"
    )


def test_school_admin_cannot_verify_other_school_payment(
    client,
    db,
    monkeypatch,
    school_admin,
    other_school_admin,
    school_two_subscription,
):
    payment = create_payment(
        db=db,
        school_id=other_school_admin.school_id,
        subscription_id=school_two_subscription.id,
        tx_ref="OTHER-SCHOOL-VERIFY",
    )

    def provider_should_not_be_called(*args, **kwargs):
        raise AssertionError(
            "Flutterwave verification should not be called"
        )

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        provider_should_not_be_called,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": "900004",
        },
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Payment transaction not found"
    )


# ============================================================
# PROVIDER VALIDATION
# ============================================================


def test_verification_rejects_transaction_reference_mismatch(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="EXPECTED-REFERENCE",
    )

    transaction_id = "900005"

    def fake_verify_transaction(received_transaction_id):
        return {
            "status": "success",
            "data": {
                "id": transaction_id,
                "tx_ref": "WRONG-REFERENCE",
                "status": "successful",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        fake_verify_transaction,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": transaction_id,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment transaction reference does not match"
    )

    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert pending_subscription.status == "pending"


def test_verification_rejects_currency_mismatch(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="CURRENCY-MISMATCH",
    )

    transaction_id = "900006"

    def fake_verify_transaction(received_transaction_id):
        return {
            "status": "success",
            "data": {
                "id": transaction_id,
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "USD",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        fake_verify_transaction,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": transaction_id,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment currency does not match"
    )

    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert pending_subscription.status == "pending"


def test_verification_rejects_underpayment(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="UNDERPAYMENT-TEST",
        amount=Decimal("20000.00"),
    )

    transaction_id = "900007"

    def fake_verify_transaction(received_transaction_id):
        return {
            "status": "success",
            "data": {
                "id": transaction_id,
                "tx_ref": payment.tx_ref,
                "status": "successful",
                "currency": "NGN",
                "amount": 15000,
            },
        }

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        fake_verify_transaction,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": transaction_id,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Payment amount is less than expected"
    )

    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert pending_subscription.status == "pending"


def test_verification_rejects_unsuccessful_provider_payment(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="FAILED-PROVIDER-PAYMENT",
    )

    transaction_id = "900008"

    def fake_verify_transaction(received_transaction_id):
        return {
            "status": "success",
            "data": {
                "id": transaction_id,
                "tx_ref": payment.tx_ref,
                "status": "failed",
                "currency": "NGN",
                "amount": 20000,
            },
        }

    monkeypatch.setattr(
        "app.services.payment_service.verify_transaction",
        fake_verify_transaction,
    )

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": transaction_id,
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Flutterwave payment is not successful"
    )

    db.refresh(payment)
    db.refresh(pending_subscription)

    assert payment.status == "pending"
    assert pending_subscription.status == "pending"


# ============================================================
# PROVIDER TRANSACTION REUSE
# ============================================================


def test_flutterwave_transaction_cannot_be_reused(
    client,
    db,
    monkeypatch,
    school_admin,
    pending_subscription,
):
    reused_transaction_id = "900009"

    existing_payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="ORIGINAL-TRANSACTION",
        payment_status="successful",
        flutterwave_transaction_id=(
            reused_transaction_id
        ),
    )

    payment = create_payment(
        db=db,
        school_id=school_admin.school_id,
        subscription_id=pending_subscription.id,
        tx_ref="SECOND-PAYMENT",
    )

    def fake_verify_transaction(received_transaction_id):
        return {
            "status": "success",
            "data": {
                "id": reused_transaction_id,
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

    token = login(
        client,
        school_admin.email,
    )

    response = client.post(
        f"/api/payments/{payment.id}/verify",
        headers=auth_headers(token),
        json={
            "transaction_id": reused_transaction_id,
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Flutterwave transaction has already "
        "been used for another payment"
    )

    db.refresh(existing_payment)
    db.refresh(payment)
    db.refresh(pending_subscription)

    assert existing_payment.status == "successful"
    assert payment.status == "pending"
    assert payment.flutterwave_transaction_id is None
    assert pending_subscription.status == "pending"



def test_payment_initialization_requires_term_closing_date(
    client,
    db,
    school_admin,
    pending_subscription,
    second_term,
):
    second_term.closing_date = None
    db.commit()

    token = login(client, school_admin.email)

    response = client.post(
        "/api/payments/initialize",
        headers=auth_headers(token),
        json={"subscription_id": pending_subscription.id},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Configure the term closing date before payment"
    )


def test_payment_initialization_rejects_elapsed_term(
    client,
    db,
    school_admin,
    pending_subscription,
    second_term,
):
    from datetime import date, timedelta

    second_term.closing_date = (
        date.today() - timedelta(days=30)
    )
    db.commit()

    token = login(client, school_admin.email)

    response = client.post(
        "/api/payments/initialize",
        headers=auth_headers(token),
        json={"subscription_id": pending_subscription.id},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "The academic term subscription period "
        "has already ended"
    )



def test_repeated_payment_verification_preserves_admin_expiration_override(
    db,
    active_subscription,
):
    from datetime import datetime, timedelta, timezone

    from app.models.payment_transaction import PaymentTransaction
    from app.services.payment_service import process_verified_payment

    # Simulate an already-activated, successfully paid subscription.
    original_expiration = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=30)
    ).replace(microsecond=0)

    admin_override_expiration = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=90)
    ).replace(microsecond=0)

    active_subscription.status = "active"
    active_subscription.activated_at = datetime.now(
        timezone.utc
    ).replace(tzinfo=None)
    active_subscription.expires_at = admin_override_expiration

    payment = PaymentTransaction(
        school_id=active_subscription.school_id,
        subscription_id=active_subscription.id,
        tx_ref="TEST-OVERRIDE-PRESERVATION-001",
        flutterwave_transaction_id="987654321",
        status="successful",
        verified_at=datetime.now(timezone.utc).replace(tzinfo=None),
        amount=1000,
        currency="NGN",
    )

    db.add(payment)
    db.commit()

    # Reprocess the same successful transaction.
    returned_payment, returned_subscription = process_verified_payment(
        db=db,
        payment=payment,
        subscription=active_subscription,
        transaction_id="987654321",
    )

    assert returned_payment.id == payment.id
    assert returned_subscription.id == active_subscription.id

    db.refresh(active_subscription)

    # The existing administrator-approved expiration must survive.
    assert active_subscription.expires_at == admin_override_expiration
    assert active_subscription.status == "active"
