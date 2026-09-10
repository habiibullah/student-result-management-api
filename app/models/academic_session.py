from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AcademicSession(Base):
    __tablename__ = "academic_sessions"

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "name",
            name="uq_academic_sessions_school_name",
        ),
        Index(
            "uq_academic_sessions_one_current_per_school",
            "school_id",
            unique=True,
            postgresql_where=text("is_current = true"),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    teaching_assignments: Mapped[list["TeachingAssignment"]] = relationship(
        back_populates="academic_session",
        cascade="all, delete-orphan",
    )
