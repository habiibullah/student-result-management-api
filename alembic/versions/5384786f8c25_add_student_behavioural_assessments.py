"""add student behavioural assessments

Revision ID: 5384786f8c25
Revises: 5affe3dabd9a
Create Date: 2026-09-24 18:22:20.029808

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5384786f8c25'
down_revision: Union[str, Sequence[str], None] = '5affe3dabd9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_behavioural_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "academic_session_id",
            sa.Integer(),
            sa.ForeignKey("academic_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "term_id",
            sa.Integer(),
            sa.ForeignKey("terms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *[
            sa.Column(field, sa.Integer(), nullable=True)
            for field in (
                "punctuality",
                "neatness",
                "honesty",
                "politeness",
                "attentiveness",
                "cooperation",
            )
        ],
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "student_id",
            "academic_session_id",
            "term_id",
            name="uq_student_behavioural_assessment_session_term",
        ),
        *[
            sa.CheckConstraint(
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
        ],
    )


def downgrade() -> None:
    op.drop_table("student_behavioural_assessments")
