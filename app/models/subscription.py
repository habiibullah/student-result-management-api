from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "academic_session_id",
            "term_id",
            name="uq_subscription_school_session_term",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    school_id: Mapped[int] = mapped_column(
        ForeignKey(
            "schools.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    subscription_plan_id: Mapped[int] = mapped_column(
        ForeignKey(
            "subscription_plans.id",
        ),
        nullable=False,
        index=True,
    )

    academic_session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "academic_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    term_id: Mapped[int] = mapped_column(
        ForeignKey(
            "terms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "active",
            "expired",
            "cancelled",
            name="subscription_status",
        ),
        nullable=False,
        default="pending",
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
