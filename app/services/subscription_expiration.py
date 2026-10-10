
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status


GRACE_PERIOD_DAYS = 14
SCHOOL_TIMEZONE = ZoneInfo("Africa/Lagos")


def calculate_subscription_expiration(
    closing_date: date | None,
    *,
    activated_at: datetime | None = None,
) -> datetime:
    """
    Calculate the exclusive UTC expiration timestamp.

    A subscription remains valid through the 14th calendar
    day after the school's official term closing date.

    Return a naive UTC datetime to match the existing
    database DateTime columns.
    """
    if closing_date is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Configure the term closing date before payment",
        )

    final_access_date = closing_date + timedelta(
        days=GRACE_PERIOD_DAYS
    )

    expiration_local = datetime.combine(
        final_access_date + timedelta(days=1),
        time.min,
        tzinfo=SCHOOL_TIMEZONE,
    )

    expiration_utc = expiration_local.astimezone(
        timezone.utc
    ).replace(tzinfo=None)

    if activated_at is not None:
        activation_utc = (
            activated_at.astimezone(timezone.utc)
            .replace(tzinfo=None)
            if activated_at.tzinfo is not None
            else activated_at
        )

        if expiration_utc <= activation_utc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "The academic term subscription period "
                    "has already ended"
                ),
            )

    return expiration_utc
