from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription import Subscription


def require_active_term_subscription(
    db: Session,
    school_id: int,
    academic_session_id: int,
    term_id: int,
) -> Subscription:
    subscription = db.scalar(
        select(Subscription).where(
            Subscription.school_id == school_id,
            Subscription.academic_session_id == academic_session_id,
            Subscription.term_id == term_id,
            Subscription.status == "active",
        )
    )


    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "An active subscription is required "
                "for this academic term"
            ),
        )

    # Subscription timestamps are stored as naive UTC.
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Temporarily preserve access for legacy subscriptions
    # that were activated before expiration tracking existed.
    if (
        subscription.expires_at is not None
        and subscription.expires_at <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The subscription for this academic term has expired",
        )

    return subscription
