import base64
import hashlib
import hmac
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings

from app.core.dependencies import require_school_admin
from app.database.connection import get_db
from app.models.payment_transaction import PaymentTransaction
from app.models.school import School
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.schemas.payment import (
    PaymentInitializeRequest,
    PaymentInitializeResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
    PaymentTransactionResponse,

)
from app.services.flutterwave_service import (
    FlutterwaveServiceError,
    initialize_payment,
    verify_transaction,
)
from app.services.payment_service import process_verified_payment

router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"],
)


@router.post(
    "/initialize",
    response_model=PaymentInitializeResponse,
)
def initialize_subscription_payment(
    payload: PaymentInitializeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    school_id = current_user.school_id

    subscription = db.scalar(
        select(Subscription).where(
            Subscription.id == payload.subscription_id,
            Subscription.school_id == school_id,
        )
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Payment can only be initialized for "
                "a pending subscription"
            ),
        )

    plan = db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id
            == subscription.subscription_plan_id
        )
    )

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found",
        )

    school = db.scalar(
        select(School).where(
            School.id == school_id,
        )
    )

    if school is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        )

    successful_payment = db.scalar(
        select(PaymentTransaction).where(
            PaymentTransaction.subscription_id
            == subscription.id,
            PaymentTransaction.school_id == school_id,
            PaymentTransaction.status == "successful",
        )
    )

    if successful_payment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This subscription already has a "
                "successful payment"
            ),
        )

    pending_payment = db.scalar(
        select(PaymentTransaction)
        .where(
            PaymentTransaction.subscription_id
            == subscription.id,
            PaymentTransaction.school_id == school_id,
            PaymentTransaction.status == "pending",
            PaymentTransaction.payment_link.is_not(None),
        )
        .order_by(
            PaymentTransaction.created_at.desc()
        )
    )

    if pending_payment is not None:
        return PaymentInitializeResponse(
            payment_id=pending_payment.id,
            subscription_id=subscription.id,
            tx_ref=pending_payment.tx_ref,
            amount=pending_payment.amount,
            currency=pending_payment.currency,
            status=pending_payment.status,
            payment_link=pending_payment.payment_link,
        )

    tx_ref = (
        f"SRMS-S{school_id}-SUB{subscription.id}-"
        f"{uuid4().hex}"
    )

    payment = PaymentTransaction(
        school_id=school_id,
        subscription_id=subscription.id,
        tx_ref=tx_ref,
        amount=plan.price_per_term,
        currency="NGN",
        status="pending",
        payment_provider="flutterwave",
    )

    db.add(payment)
    db.flush()

    try:
        flutterwave_response = initialize_payment(
            tx_ref=tx_ref,
            amount=str(plan.price_per_term),
            currency="NGN",
            customer_email=current_user.email,
            customer_name=school.name,
            customer_phone=school.phone,
            subscription_id=subscription.id,
        )

    except FlutterwaveServiceError as exc:
        payment.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    payment_link = (
        flutterwave_response["data"]["link"]
    )

    payment.payment_link = payment_link

    db.commit()
    db.refresh(payment)

    return PaymentInitializeResponse(
        payment_id=payment.id,
        subscription_id=subscription.id,
        tx_ref=payment.tx_ref,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        payment_link=payment.payment_link,
    )


@router.post(
    "/{payment_id}/verify",
    response_model=PaymentVerifyResponse,
)
    
def verify_subscription_payment(
    payment_id: int,
    payload: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
    ):
    school_id = current_user.school_id

    payment = db.scalar(
        select(PaymentTransaction).where(
            PaymentTransaction.id == payment_id,
            PaymentTransaction.school_id == school_id,
        )
    )

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment transaction not found",
        )

    subscription = db.scalar(
        select(Subscription).where(
            Subscription.id == payment.subscription_id,
            Subscription.school_id == school_id,
        )
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    payment, subscription = process_verified_payment(
        db=db,
        payment=payment,
        subscription=subscription,
        transaction_id=payload.transaction_id,
    )

    return PaymentVerifyResponse(
        payment_id=payment.id,
        subscription_id=subscription.id,
        flutterwave_transaction_id=(
            payment.flutterwave_transaction_id
        ),
        payment_status=payment.status,
        subscription_status=subscription.status,
        verified_at=payment.verified_at,
    )
@router.get(
    "",
    response_model=list[PaymentTransactionResponse],
)
def list_school_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    """
    Return payment transactions belonging only to the
    authenticated school administrator's school.
    """

    payments = (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.school_id == current_user.school_id
        )
        .order_by(PaymentTransaction.created_at.desc())
        .all()
    )

    return payments


@router.get(
    "/{payment_id}",
    response_model=PaymentTransactionResponse,
)
def get_school_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    """
    Return one payment transaction belonging to the
    authenticated school administrator's school.
    """

    payment = (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.id == payment_id,
            PaymentTransaction.school_id == current_user.school_id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment transaction not found",
        )

    return payment



@router.post("/webhook")
async def flutterwave_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive and securely process Flutterwave payment webhooks.

    Supports:
    - Flutterwave v3 `verif-hash` authentication
    - Flutterwave HMAC-SHA256 `flutterwave-signature` authentication

    A webhook never activates a subscription based only on the payload.
    The transaction is always re-verified with Flutterwave first.
    """

    raw_body = await request.body()

    secret_hash = settings.flutterwave_secret_hash

    if not secret_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Flutterwave secret hash is not configured",
        )

    # ---------------------------------------------------------
    # 1. Authenticate webhook
    # ---------------------------------------------------------

    verif_hash = request.headers.get("verif-hash")
    signature = request.headers.get("flutterwave-signature")

    is_valid = False

    # Flutterwave v3 webhook authentication
    if verif_hash:
        is_valid = hmac.compare_digest(
            verif_hash,
            secret_hash,
        )

    # Newer Flutterwave webhook authentication
    elif signature:
        expected_signature = base64.b64encode(
            hmac.new(
                secret_hash.encode(),
                raw_body,
                hashlib.sha256,
            ).digest()
        ).decode()

        is_valid = hmac.compare_digest(
            expected_signature,
            signature,
        )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Flutterwave webhook authentication",
        )

    # ---------------------------------------------------------
    # 2. Parse webhook payload
    # ---------------------------------------------------------

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook JSON payload",
        )

    event = payload.get("event") or payload.get("type")
    data = payload.get("data")

    if not isinstance(data, dict):
        return {
            "status": "ignored",
            "reason": "Missing webhook data",
        }

    # Support both v3 and newer event naming
    valid_events = {
        "charge.completed",
        "charge.completed.successful",
    }

    if event not in valid_events:
        return {
            "status": "ignored",
            "reason": "Unsupported event",
        }

    transaction_id = data.get("id")
    tx_ref = data.get("tx_ref") or data.get("reference")

    if not transaction_id or not tx_ref:
        return {
            "status": "ignored",
            "reason": "Missing transaction identifier",
        }

    transaction_id = str(transaction_id)

    # ---------------------------------------------------------
    # 3. Find our local payment transaction
    # ---------------------------------------------------------

    payment = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.tx_ref == tx_ref)
        .first()
    )

    if not payment:
        return {
            "status": "ignored",
            "reason": "Unknown transaction reference",
        }

    # ---------------------------------------------------------
    # 4. Idempotency
    # ---------------------------------------------------------

    if payment.status == "successful":
        return {
            "status": "already_processed",
            "payment_id": payment.id,
        }

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.id == payment.subscription_id,
            Subscription.school_id == payment.school_id,
        )
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.status != "pending":
        return {
            "status": "ignored",
            "reason": "Subscription is no longer pending",
        }

    # ---------------------------------------------------------
    # 5. Verify transaction directly with Flutterwave
    # ---------------------------------------------------------

    try:
        verification = verify_transaction(transaction_id)
    except FlutterwaveServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Flutterwave verification failed: {exc}",
        )

    verified_data = verification.get("data")

    if not isinstance(verified_data, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid Flutterwave verification response",
        )

    verified_transaction_id = verified_data.get("id")
    verified_tx_ref = (
        verified_data.get("tx_ref")
        or verified_data.get("reference")
    )
    verified_status = verified_data.get("status")
    verified_currency = verified_data.get("currency")
    verified_amount = verified_data.get("amount")

    # ---------------------------------------------------------
    # 6. Validate Flutterwave verification result
    # ---------------------------------------------------------

    if str(verified_transaction_id) != transaction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flutterwave transaction ID mismatch",
        )

    if verified_tx_ref != payment.tx_ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flutterwave transaction reference mismatch",
        )

    if verified_status != "successful":
        return {
            "status": "ignored",
            "reason": "Transaction is not successful",
        }

    if verified_currency != payment.currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment currency mismatch",
        )

    try:
        received_amount = Decimal(str(verified_amount))
        expected_amount = Decimal(str(payment.amount))
    except (InvalidOperation, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment amount",
        )

    if received_amount < expected_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient payment amount",
        )

    # ---------------------------------------------------------
    # 7. Prevent reuse of Flutterwave transaction ID
    # ---------------------------------------------------------

    existing_payment = (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.flutterwave_transaction_id
            == transaction_id,
            PaymentTransaction.id != payment.id,
        )
        .first()
    )

    if existing_payment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Flutterwave transaction has already been used",
        )

    # ---------------------------------------------------------
    # 8. Activate payment and subscription atomically
    # ---------------------------------------------------------

    now = datetime.utcnow()

    payment.flutterwave_transaction_id = transaction_id
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process payment webhook",
        )

    # ---------------------------------------------------------
    # 9. Acknowledge Flutterwave
    # ---------------------------------------------------------

    return {
        "status": "processed",
        "payment_id": payment.id,
        "subscription_id": subscription.id,
        "payment_status": payment.status,
        "subscription_status": subscription.status,
    }
