from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class GradingScale(Base):
    __tablename__ = "grading_scales"

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "grade",
            name="uq_grading_scale_school_grade",
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

    grade: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    minimum_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    maximum_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    remark: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
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
