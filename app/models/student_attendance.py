from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class StudentAttendance(Base):
    __tablename__ = "student_attendance"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "academic_session_id",
            "term_id",
            name="uq_student_attendance_session_term",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
    )

    academic_session_id: Mapped[int] = mapped_column(
        ForeignKey("academic_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    term_id: Mapped[int] = mapped_column(
        ForeignKey("terms.id", ondelete="CASCADE"),
        nullable=False,
    )

    school_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    days_present: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    days_absent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
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

    student: Mapped["Student"] = relationship()
    academic_session: Mapped["AcademicSession"] = relationship()
    term: Mapped["Term"] = relationship()
