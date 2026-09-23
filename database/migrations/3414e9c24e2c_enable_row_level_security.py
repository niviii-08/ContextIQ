"""enable row level security

Adds Supabase Row Level Security (RLS) policies so that, once the app
switches from the dev X-User-Id header to real Supabase Auth (see
app/core/deps.py), every table is defended in depth at the database level
in addition to the application-level user_id filtering already done in
app/services/*.

Convention: `users.id` is expected to equal Supabase's `auth.uid()`. Every
other table is isolated on its own `user_id` column via `auth.uid()`.

Revision ID: 3414e9c24e2c
Revises: ecbe5615243f
Create Date: 2026-08-18 07:46:22.042467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3414e9c24e2c'
down_revision: Union[str, None] = 'ecbe5615243f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables isolated by their own `user_id` column.
_USER_ID_TABLES = [
    "locations",
    "tasks",
    "task_events",
    "interruptions",
    "context_sessions",
    "task_associations",
    "predictions",
    "recommendations",
    "behaviour_metrics",
]


def upgrade() -> None:
    # --- local/dev compatibility shim ---
    # On Supabase, `auth.uid()` already exists and returns the JWT subject.
    # On a plain local/Docker Postgres (no Supabase), that function doesn't
    # exist, which would make this migration fail. This creates a
    # STUB ONLY IF ONE ISN'T ALREADY PRESENT, so real Supabase behaviour is
    # never overridden, while local `docker-compose` Postgres still gets a
    # harmless auth.uid() that returns NULL (RLS policies below then simply
    # allow no rows through until the app sets an app-level equivalent,
    # which is fine — the API layer already filters by user_id itself).
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE p.proname = 'uid' AND n.nspname = 'auth'
            ) THEN
                EXECUTE 'CREATE SCHEMA IF NOT EXISTS auth';
                EXECUTE $def$
                    CREATE FUNCTION auth.uid() RETURNS uuid
                    LANGUAGE sql STABLE
                    AS $body$ SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid $body$
                $def$;
            END IF;
        END $$;
        """
    )

    # --- users table: a row is visible/editable only by the user it represents ---
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY users_isolation ON users
        USING (id = auth.uid())
        WITH CHECK (id = auth.uid());
        """
    )

    # --- every other table: isolated on user_id ---
    for table in _USER_ID_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            CREATE POLICY {table}_isolation ON {table}
            USING (user_id = auth.uid())
            WITH CHECK (user_id = auth.uid());
            """
        )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS users_isolation ON users;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")

    for table in _USER_ID_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
