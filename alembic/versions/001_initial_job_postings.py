"""Initial job_postings table — reflects existing production schema.

This migration documents the current DB state. It should be stamped (not
executed) against existing databases that already have the table.

Revision ID: 001
Revises:
Create Date: 2026-05-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "job_postings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("record_id", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("company_inferred", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.Column("location", postgresql.JSONB(), nullable=True),
        sa.Column("salary", postgresql.JSONB(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_length", sa.Integer(), nullable=True),
        sa.Column("job_category", postgresql.JSONB(), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=True),
        sa.Column("post_date", sa.Date(), nullable=True),
        sa.Column("post_date_raw", sa.Text(), nullable=True),
        sa.Column("link", sa.Text(), nullable=True),
        sa.Column("contact", sa.Text(), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("record_id"),
    )

    op.create_index("idx_jp_source", "job_postings", ["source"])
    op.create_index("idx_jp_post_date", "job_postings", ["post_date"])
    op.create_index("idx_jp_language", "job_postings", ["language"])
    op.create_index("idx_jp_company", "job_postings", ["company"])

    op.execute(
        "CREATE INDEX idx_jp_location_city ON job_postings ((location->>'city'))"
    )
    op.execute(
        "CREATE INDEX idx_jp_location_state ON job_postings ((location->>'state'))"
    )
    op.execute(
        "CREATE INDEX idx_jp_salary_min ON job_postings ((salary->>'min'))"
    )
    op.execute(
        "CREATE INDEX idx_jp_salary_max ON job_postings ((salary->>'max'))"
    )
    op.execute(
        "CREATE INDEX idx_jp_salary_unit ON job_postings ((salary->>'unit'))"
    )

    op.execute(
        "CREATE INDEX idx_jp_location_gin ON job_postings USING GIN (location)"
    )
    op.execute(
        "CREATE INDEX idx_jp_salary_gin ON job_postings USING GIN (salary)"
    )
    op.execute(
        "CREATE INDEX idx_jp_category_gin ON job_postings USING GIN (job_category)"
    )

    op.execute(
        "CREATE INDEX idx_jp_title_trgm ON job_postings USING GIN (title gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX idx_jp_description_trgm ON job_postings USING GIN (description gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX idx_jp_company_trgm ON job_postings USING GIN (company gin_trgm_ops)"
    )


def downgrade() -> None:
    op.drop_index("idx_jp_company_trgm", table_name="job_postings")
    op.drop_index("idx_jp_description_trgm", table_name="job_postings")
    op.drop_index("idx_jp_title_trgm", table_name="job_postings")
    op.drop_index("idx_jp_category_gin", table_name="job_postings")
    op.drop_index("idx_jp_salary_gin", table_name="job_postings")
    op.drop_index("idx_jp_location_gin", table_name="job_postings")
    op.drop_index("idx_jp_salary_unit", table_name="job_postings")
    op.drop_index("idx_jp_salary_max", table_name="job_postings")
    op.drop_index("idx_jp_salary_min", table_name="job_postings")
    op.drop_index("idx_jp_location_state", table_name="job_postings")
    op.drop_index("idx_jp_location_city", table_name="job_postings")
    op.drop_index("idx_jp_company", table_name="job_postings")
    op.drop_index("idx_jp_language", table_name="job_postings")
    op.drop_index("idx_jp_post_date", table_name="job_postings")
    op.drop_index("idx_jp_source", table_name="job_postings")
    op.drop_table("job_postings")
