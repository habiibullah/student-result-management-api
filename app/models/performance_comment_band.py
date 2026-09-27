from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PerformanceCommentBand(Base):
    __tablename__ = "performance_comment_bands"

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

    minimum_average: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    maximum_average: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    teacher_comment: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    principal_comment: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
