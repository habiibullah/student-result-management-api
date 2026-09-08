from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PublishedReportSnapshot(Base):
    __tablename__ = "published_report_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "publication_id",
            "student_id",
            name="uq_published_report_snapshot_publication_student",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    publication_id: Mapped[int] = mapped_column(
        ForeignKey(
            "result_publications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey(
            "students.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    report_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
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

    publication: Mapped["ResultPublication"] = relationship()
    student: Mapped["Student"] = relationship()
