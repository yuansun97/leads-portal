"""add reached_out claim fields

Revision ID: 002_reached_out_claim
Revises: 001_initial
Create Date: 2026-08-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_reached_out_claim"
down_revision: Union[str, Sequence[str], None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("reached_out_by", sa.String(length=128), nullable=True))
    op.add_column("leads", sa.Column("reached_out_by_email", sa.String(length=320), nullable=True))
    op.add_column("leads", sa.Column("reached_out_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "reached_out_at")
    op.drop_column("leads", "reached_out_by_email")
    op.drop_column("leads", "reached_out_by")
