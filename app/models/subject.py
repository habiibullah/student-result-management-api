from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "name",
            name="uq_subjects_school_name",
        ),
        UniqueConstraint(
            "school_id",
            "code",
            name="uq_subjects_school_code",
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
        String(100),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
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

    teaching_assignments: Mapped[list["TeachingAssignment"]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
    )
