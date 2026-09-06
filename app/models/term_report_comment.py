from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TermReportComment(Base):
    __tablename__ = "term_report_comments"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "academic_session_id",
            "term_id",
            name="uq_student_session_term_report_comment",
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

    teacher_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    principal_comment: Mapped[str | None] = mapped_column(
        Text,
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

    student: Mapped["Student"] = relationship()
    academic_session: Mapped["AcademicSession"] = relationship()
    term: Mapped["Term"] = relationship()
