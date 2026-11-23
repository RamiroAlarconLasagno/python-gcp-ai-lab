# migrations/versions/0001_quotes_table.py
"""Crea la extensión vector (para el RAG) y la tabla quotes.

Revision ID: 0001
Revises:
Create Date: 2026-11-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crea la extensión vector y la tabla quotes."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "quotes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("zone", sa.String(32), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("actual_weight_kg", sa.Numeric(), nullable=False),
        sa.Column("volumetric_weight_kg", sa.Numeric(), nullable=False),
        sa.Column("billable_weight_kg", sa.Numeric(), nullable=False),
        sa.Column("length_cm", sa.Numeric(), nullable=False),
        sa.Column("width_cm", sa.Numeric(), nullable=False),
        sa.Column("height_cm", sa.Numeric(), nullable=False),
        sa.Column("freight", sa.Numeric(12, 2), nullable=False),
        sa.Column("urgent_surcharge", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("delivery_days", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    """Borra la tabla quotes y la extensión vector."""
    op.drop_table("quotes")
    op.execute("DROP EXTENSION IF EXISTS vector")
