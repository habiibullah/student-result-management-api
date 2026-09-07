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


class ResultPublication(Base):
    __tablename__ = "result_publications"

    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "academic_session_id",
            "term_id",
            name="uq_result_publication_class_session_term",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    class_id: Mapped[int] = mapped_column(
        ForeignKey(
            "classes.id",
            ondelete="CASCADE",
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
        String(20),
        nullable=False,
        default="published",
    )

    published_by_user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    published_at: Mapped[datetime] = mapped_column(
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

    class_: Mapped["Class"] = relationship()
    academic_session: Mapped["AcademicSession"] = relationship()
    term: Mapped["Term"] = relationship()
    published_by: Mapped["User"] = relationship()
