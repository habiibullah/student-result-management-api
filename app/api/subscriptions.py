from datetime import datetime

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
from app.models.subscription_plan import SubscriptionPlan
from app.models.term import Term
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionStatusUpdate,
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

    subscription.status = normalized_status

    if normalized_status == "active":
        if subscription.activated_at is None:
            subscription.activated_at = datetime.utcnow()

    elif (
        normalized_status == "pending"
        and current_status == "cancelled"
    ):

        subscription.activated_at = None

    db.commit()
    db.refresh(subscription)

    return subscription
