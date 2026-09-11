from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment_transaction import PaymentTransaction
from app.models.subscription import Subscription
from app.services.flutterwave_service import (
    FlutterwaveServiceError,
    verify_transaction,
)


def process_verified_payment(
    db: Session,
    payment: PaymentTransaction,
    subscription: Subscription,
    transaction_id: str,
) -> tuple[PaymentTransaction, Subscription]:
    """
    Verify a Flutterwave transaction and, if valid,
    mark the payment successful and activate its subscription.

    This function is shared by manual verification and webhook processing.
    """

    transaction_id = str(transaction_id)

    # ---------------------------------------------------------
    # 1. Idempotency
    # ---------------------------------------------------------

    if payment.status == "successful":
        if payment.flutterwave_transaction_id != transaction_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Payment has already been verified "
                    "with another transaction"
                ),
            )

        if payment.verified_at is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Verified payment has no verification timestamp",
            )

        return payment, subscription

    # ---------------------------------------------------------
    # 2. Subscription must still be pending
    # ---------------------------------------------------------

    if subscription.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The subscription is no longer pending "
                "and cannot be activated by this payment"
            ),
        )

    # ---------------------------------------------------------
    # 3. Verify directly with Flutterwave
    # ---------------------------------------------------------

    try:
        flutterwave_response = verify_transaction(transaction_id)
    except FlutterwaveServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    data = flutterwave_response.get("data")

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Flutterwave returned an invalid verification response",
        )

    # ---------------------------------------------------------
    # 4. Validate provider transaction
    # ---------------------------------------------------------

    provider_transaction_id = str(data.get("id", ""))

    if provider_transaction_id != transaction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flutterwave transaction ID does not match",
        )

    provider_tx_ref = (
        data.get("tx_ref")
        or data.get("reference")
    )

    if provider_tx_ref != payment.tx_ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment transaction reference does not match",
        )

    if data.get("status") != "successful":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Flutterwave payment is not successful",
        )

    returned_currency = str(
        data.get("currency", "")
    ).upper()

    if returned_currency != payment.currency.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment currency does not match",
        )

    try:
        returned_amount = Decimal(
            str(data.get("amount"))
        )
    except (InvalidOperation, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Flutterwave returned an invalid payment amount",
        )

    if returned_amount < payment.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount is less than expected",
        )

    # ---------------------------------------------------------
    # 5. Prevent provider transaction reuse
    # ---------------------------------------------------------

    existing_provider_transaction = db.scalar(
        select(PaymentTransaction).where(
            PaymentTransaction.flutterwave_transaction_id
            == provider_transaction_id,
            PaymentTransaction.id != payment.id,
        )
    )

    if existing_provider_transaction is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Flutterwave transaction has already "
                "been used for another payment"
            ),
        )

    # ---------------------------------------------------------
    # 6. Activate payment and subscription
    # ---------------------------------------------------------

    now = datetime.utcnow()

    payment.flutterwave_transaction_id = provider_transaction_id
    payment.status = "successful"
    payment.verified_at = now

    subscription.status = "active"

    if subscription.activated_at is None:
        subscription.activated_at = now

    try:
        db.commit()
        db.refresh(payment)
        db.refresh(subscription)

    except Exception:
        db.rollback()
        raise

    return payment, subscription
