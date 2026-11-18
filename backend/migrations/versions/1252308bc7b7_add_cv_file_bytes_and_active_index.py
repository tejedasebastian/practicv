"""add cv file bytes and active index

Revision ID: 1252308bc7b7
Revises: 3ba0135828de
Create Date: 2026-11-17 20:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1252308bc7b7"
down_revision: str | Sequence[str] | None = "3ba0135828de"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cv_documents", sa.Column("file_bytes", sa.LargeBinary(), nullable=True))
    op.create_index(
        "uq_cv_documents_active_profile",
        "cv_documents",
        ["profile_id"],
        unique=True,
        postgresql_where=sa.text("is_active"),
    )


def downgrade() -> None:
    op.drop_index("uq_cv_documents_active_profile", table_name="cv_documents")
    op.drop_column("cv_documents", "file_bytes")
