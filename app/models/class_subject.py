from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ClassSubject(Base):
    __tablename__ = "class_subjects"

    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "subject_id",
            "academic_session_id",
            name="uq_class_subject_session",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    academic_session_id: Mapped[int] = mapped_column(
        ForeignKey("academic_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    class_: Mapped["Class"] = relationship(
        back_populates="class_subjects",
    )

    subject: Mapped["Subject"] = relationship(
        back_populates="class_subjects",
    )

    academic_session: Mapped["AcademicSession"] = relationship(
        back_populates="class_subjects",
    )
