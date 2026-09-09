from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ReportSettings(Base):
    __tablename__ = "report_settings"

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            name="uq_report_settings_school",
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

    report_title: Mapped[str] = mapped_column(
        String(255),
        default="Student Report Sheet",
        nullable=False,
    )

    show_class_position: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    show_class_size: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    show_attendance: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    show_teacher_comment: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    show_principal_comment: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    show_school_motto: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    show_school_logo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    show_grading_remarks: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    principal_designation: Mapped[str] = mapped_column(
        String(100),
        default="Principal",
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
