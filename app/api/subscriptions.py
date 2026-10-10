from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    require_platform_admin,
    require_school_admin,
)
from app.database.connection import get_db
from app.models.academic_session import AcademicSession
from app.models.subscription import Subscription
from app.models.subscription_expiration_override import (
    SubscriptionExpirationOverride as SubscriptionExpirationOverrideRecord,
)
from app.models.subscription_plan import SubscriptionPlan
from app.models.term import Term
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionExpirationOverride,
    SubscriptionResponse,
    SubscriptionStatusUpdate,
)
from app.services.subscription_expiration import (
    calculate_subscription_expiration,
)


router = APIRouter(
    prefix="/api/subscriptions",
    tags=["Subscriptions"],
)


@router.post(
    "",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    school_id = current_user.school_id

    plan = db.scalar(
        select(SubscriptionPlan).where(
            SubscriptionPlan.id
            == payload.subscription_plan_id,
            SubscriptionPlan.is_active.is_(True),
        )
    )

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active subscription plan not found",
        )

    academic_session = db.scalar(
        select(AcademicSession).where(
            AcademicSession.id
            == payload.academic_session_id,
            AcademicSession.school_id == school_id,
        )
    )

    if academic_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    term = db.scalar(
        select(Term)
        .join(
            AcademicSession,
            Term.academic_session_id
            == AcademicSession.id,
        )
        .where(
            Term.id == payload.term_id,
            Term.academic_session_id
            == payload.academic_session_id,
            AcademicSession.school_id == school_id,
        )
    )

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found for this academic session",
        )

    existing_subscription = db.scalar(
        select(Subscription).where(
            Subscription.school_id == school_id,
            Subscription.academic_session_id
            == payload.academic_session_id,
            Subscription.term_id == payload.term_id,
        )
    )

    if existing_subscription is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A subscription already exists for "
                "this school, academic session, and term"
            ),
        )

    subscription = Subscription(
        school_id=school_id,
        subscription_plan_id=plan.id,
        academic_session_id=academic_session.id,
        term_id=term.id,
        status="pending",
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription


@router.get(
    "/me",
    response_model=list[SubscriptionResponse],
)
def list_school_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    return list(
        db.scalars(
            select(Subscription)
            .where(
                Subscription.school_id
                == current_user.school_id
            )
            .order_by(
                Subscription.created_at.desc()
            )
        ).all()
    )


@router.get(
    "/me/{subscription_id}",
    response_model=SubscriptionResponse,
)
def get_school_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_school_admin),
):
    subscription = db.scalar(
        select(Subscription).where(
            Subscription.id == subscription_id,
            Subscription.school_id
            == current_user.school_id,
        )
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    return subscription


@router.get(
    "",
    response_model=list[SubscriptionResponse],
)
def list_all_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_platform_admin
    ),
):
    return list(
        db.scalars(
            select(Subscription).order_by(
                Subscription.created_at.desc()
            )
        ).all()
    )


@router.patch(
    "/{subscription_id}/status",
    response_model=SubscriptionResponse,
)
def update_subscription_status(
    subscription_id: int,
    payload: SubscriptionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_platform_admin
    ),
):
    allowed_statuses = {
        "pending",
        "active",
        "expired",
        "cancelled",
    }

    normalized_status = (
        payload.status.strip().lower()
    )

    if normalized_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Status must be pending, active, "
                "expired, or cancelled"
            ),
        )

    subscription = db.scalar(
        select(Subscription).where(
            Subscription.id == subscription_id
        )
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    allowed_transitions = {
    "pending": {"active", "cancelled"},
    "active": {"expired", "cancelled"},
    "cancelled": {"pending"},
    "expired": set(),
    }

    current_status = subscription.status.strip().lower()

    # Allow an idempotent request that keeps the same status.
    if normalized_status != current_status:
        valid_next_statuses = allowed_transitions.get(
            current_status,
            set(),
        )

        if normalized_status not in valid_next_statuses:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Subscription status cannot change from "
                    f"'{current_status}' to '{normalized_status}'"
                ),
            )


    if normalized_status == "active" and current_status != "active":
        term = db.scalar(
            select(Term).where(
                Term.id == subscription.term_id,
                Term.academic_session_id
                == subscription.academic_session_id,
            )
        )

        if term is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription academic term not found",
            )

        activated_at = datetime.utcnow()

        expiration = calculate_subscription_expiration(
            term.closing_date,
            activated_at=activated_at,
        )

        subscription.activated_at = activated_at
        subscription.expires_at = expiration

    subscription.status = normalized_status

    if (
        normalized_status == "pending"
        and current_status == "cancelled"
    ):
        subscription.activated_at = None
        subscription.expires_at = None

    db.commit()
    db.refresh(subscription)

    return subscription



@router.patch(
    "/{subscription_id}/expiration",
    response_model=SubscriptionResponse,
)
def override_subscription_expiration(
    subscription_id: int,
    payload: SubscriptionExpirationOverride,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_platform_admin),
):
    # Require an explicit timezone to prevent ambiguous dates.
    if payload.expires_at.tzinfo is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Expiration date must include a timezone",
        )

    new_expiration = payload.expires_at.astimezone(
        timezone.utc
    ).replace(tzinfo=None)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if new_expiration <= now:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="New expiration date must be in the future",
        )

    reason = payload.reason.strip()

    if len(reason) < 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Reason must contain at least 10 characters",
        )

    subscription = db.scalar(
        select(Subscription)
        .where(Subscription.id == subscription_id)
        .with_for_update()
    )

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.status.strip().lower() != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only active subscriptions can be adjusted",
        )

    previous_expiration = subscription.expires_at

    if previous_expiration == new_expiration:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="New expiration must differ from current expiration",
        )

    audit_record = SubscriptionExpirationOverrideRecord(
        subscription_id=subscription.id,
        admin_user_id=current_user.id,
        previous_expires_at=previous_expiration,
        new_expires_at=new_expiration,
        reason=reason,
    )

    subscription.expires_at = new_expiration
    db.add(audit_record)

    db.commit()
    db.refresh(subscription)

    return subscription
