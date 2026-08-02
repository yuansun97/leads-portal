"""deny PostgREST access: RLS + revoke anon/authenticated

Revision ID: 003_rls_revoke_postgrest
Revises: 002_reached_out_claim
Create Date: 2026-08-02
"""

from typing import Sequence, Union

from alembic import op

revision: str = "003_rls_revoke_postgrest"
down_revision: Union[str, None] = "002_reached_out_claim"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("alter table public.leads enable row level security")
    op.execute("alter table public.email_outbox enable row level security")
    op.execute("revoke all on table public.leads from anon, authenticated")
    op.execute("revoke all on table public.email_outbox from anon, authenticated")
    op.execute("grant all on table public.leads to postgres, service_role")
    op.execute("grant all on table public.email_outbox to postgres, service_role")


def downgrade() -> None:
    # Restore typical Supabase defaults for public tables (prefer re-applying
    # explicit policies in a follow-up rather than relying on this).
    op.execute("grant select, insert, update, delete on table public.leads to anon, authenticated")
    op.execute(
        "grant select, insert, update, delete on table public.email_outbox to anon, authenticated"
    )
    op.execute("alter table public.leads disable row level security")
    op.execute("alter table public.email_outbox disable row level security")
