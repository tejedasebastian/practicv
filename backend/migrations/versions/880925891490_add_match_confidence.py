"""add match confidence

Revision ID: 880925891490
Revises: 4fc463903bcf
Create Date: 2026-11-17 21:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "880925891490"
down_revision: str | Sequence[str] | None = "4fc463903bcf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column("confidence", sa.Float(), server_default=sa.text("0"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("matches", "confidence")
