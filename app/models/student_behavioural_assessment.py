from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class StudentBehaviouralAssessment(Base):
    __tablename__ = "student_behavioural_assessments"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "academic_session_id",
            "term_id",
            name="uq_student_behavioural_assessment_session_term",
        ),
        *(
            CheckConstraint(
                f"{field} IS NULL OR {field} BETWEEN 1 AND 5",
                name=f"ck_behavioural_{field}_range",
            )
            for field in (
                "punctuality",
                "neatness",
                "honesty",
                "politeness",
                "attentiveness",
                "cooperation",
            )
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

    punctuality: Mapped[int | None] = mapped_column(Integer)
    neatness: Mapped[int | None] = mapped_column(Integer)
    honesty: Mapped[int | None] = mapped_column(Integer)
    politeness: Mapped[int | None] = mapped_column(Integer)
    attentiveness: Mapped[int | None] = mapped_column(Integer)
    cooperation: Mapped[int | None] = mapped_column(Integer)

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
