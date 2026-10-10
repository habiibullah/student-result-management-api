
from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException

from app.services.subscription_expiration import (
    calculate_subscription_expiration,
)


def test_expiration_includes_fourteen_day_grace_period():
    expiration = calculate_subscription_expiration(
        date(2026, 12, 18)
    )

    assert expiration == datetime(2027, 1, 1, 23, 0)


def test_expiration_handles_month_boundary():
    expiration = calculate_subscription_expiration(
        date(2026, 10, 31)
    )

    assert expiration == datetime(2026, 11, 14, 23, 0)


def test_expiration_handles_leap_year():
    expiration = calculate_subscription_expiration(
        date(2028, 2, 29)
    )

    assert expiration == datetime(2028, 3, 14, 23, 0)


def test_missing_closing_date_is_rejected():
    with pytest.raises(HTTPException) as exc_info:
        calculate_subscription_expiration(None)

    assert exc_info.value.status_code == 422


def test_expired_term_is_rejected_at_activation():
    with pytest.raises(HTTPException) as exc_info:
        calculate_subscription_expiration(
            date(2026, 1, 10),
            activated_at=datetime(2026, 10, 9),
        )

    assert exc_info.value.status_code == 409


def test_valid_term_can_be_activated():
    expiration = calculate_subscription_expiration(
        date(2026, 12, 18),
        activated_at=datetime(2026, 10, 9),
    )

    assert expiration == datetime(2027, 1, 1, 23, 0)


def test_timezone_aware_activation_is_supported():
    expiration = calculate_subscription_expiration(
        date(2026, 12, 18),
        activated_at=datetime(
            2026, 10, 9, 12, 0, tzinfo=timezone.utc
        ),
    )

    assert expiration == datetime(2027, 1, 1, 23, 0)


def test_activation_at_expiration_is_rejected():
    with pytest.raises(HTTPException) as exc_info:
        calculate_subscription_expiration(
            date(2026, 12, 18),
            activated_at=datetime(2027, 1, 1, 23, 0),
        )

    assert exc_info.value.status_code == 409
