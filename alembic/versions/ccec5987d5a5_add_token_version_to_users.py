"""add token version to users

Revision ID: ccec5987d5a5
Revises: 463ed20d470b
Create Date: 2026-09-18 16:44:12.654418
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ccec5987d5a5"
down_revision: Union[str, Sequence[str], None] = "463ed20d470b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.alter_column(
        "users",
        "token_version",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "token_version")
