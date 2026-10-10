
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SubscriptionExpirationOverride(Base):
    __tablename__ = "subscription_expiration_overrides"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id"),
        nullable=False,
        index=True,
    )

    admin_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    previous_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    new_expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ).replace(tzinfo=None),
    )
