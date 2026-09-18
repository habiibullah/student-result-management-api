"""add must change password to users

Revision ID: 463ed20d470b
Revises: 7b933b5b8b78
Create Date: 2026-09-18 15:06:56.291339

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "463ed20d470b"
down_revision: Union[str, Sequence[str], None] = "7b933b5b8b78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.alter_column(
        "users",
        "must_change_password",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        "users",
        "must_change_password",
    )
