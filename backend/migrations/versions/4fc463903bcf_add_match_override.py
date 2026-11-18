"""add match override

Revision ID: 4fc463903bcf
Revises: 1252308bc7b7
Create Date: 2026-11-17 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4fc463903bcf"
down_revision: str | Sequence[str] | None = "1252308bc7b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("overridden", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("matches", sa.Column("override_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "override_reason")
    op.drop_column("matches", "overridden")
