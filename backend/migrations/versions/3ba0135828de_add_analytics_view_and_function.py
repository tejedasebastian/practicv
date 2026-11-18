"""add analytics view and function

Revision ID: 3ba0135828de
Revises: d88dd96dd657
Create Date: 2026-11-17 20:15:11.803507

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3ba0135828de"
down_revision: str | Sequence[str] | None = "d88dd96dd657"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW v_offer_ranking AS
        WITH scored AS (
            SELECT
                o.id AS offer_id,
                o.title,
                o.company,
                o.deadline_at,
                m.profile_id,
                m.overall_score,
                m.must_have_score,
                ROW_NUMBER() OVER (
                    PARTITION BY m.profile_id
                    ORDER BY m.overall_score DESC, o.deadline_at ASC NULLS LAST
                ) AS rank
            FROM offers o
            JOIN matches m ON m.offer_id = o.id
        )
        SELECT offer_id, title, company, deadline_at, profile_id,
               overall_score, must_have_score, rank
        FROM scored
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_top_offers_for_profile(p_profile_id uuid)
        RETURNS TABLE (
            offer_id uuid,
            title text,
            company text,
            overall_score double precision,
            must_have_score double precision,
            decision text
        )
        LANGUAGE plpgsql
        STABLE
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                o.id,
                o.title::text,
                o.company::text,
                m.overall_score,
                m.must_have_score,
                m.decision::text
            FROM offers o
            JOIN matches m ON m.offer_id = o.id
            WHERE m.profile_id = p_profile_id
            ORDER BY m.overall_score DESC, o.deadline_at ASC NULLS LAST;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_matches_profile_score_covering
        ON matches (profile_id, overall_score DESC)
        INCLUDE (must_have_score, offer_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_offers_open_deadline
        ON offers (deadline_at)
        WHERE deadline_at IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_offers_open_deadline")
    op.execute("DROP INDEX IF EXISTS ix_matches_profile_score_covering")
    op.execute("DROP FUNCTION IF EXISTS fn_top_offers_for_profile(uuid)")
    op.execute("DROP VIEW IF EXISTS v_offer_ranking")
