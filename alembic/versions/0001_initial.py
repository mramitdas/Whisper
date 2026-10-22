"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-22
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("lang_code", sa.String(), nullable=True),
        sa.Column("matches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("reporter_id", sa.BigInteger(), nullable=False),
        sa.Column("reported_id", sa.BigInteger(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("session_ref", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_reports_reporter_id", "reports", ["reporter_id"])
    op.create_index("ix_reports_reported_id", "reports", ["reported_id"])
    op.create_table(
        "bans",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("matches", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("stats")
    op.drop_table("bans")
    op.drop_index("ix_reports_reported_id", table_name="reports")
    op.drop_index("ix_reports_reporter_id", table_name="reports")
    op.drop_table("reports")
    op.drop_table("users")
