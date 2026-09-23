"""add recommendation feedback table

Records explicit user feedback (ACCEPTED / DISMISSED / DEFERRED) on
recommendations, including an optional link to the task that was created
as a result and any free-text note the user left. Powers the closed-loop
improvement pipeline for the recommendation engine.

Revision ID: 9f82d6a11b3c
Revises: 3414e9c24e2c
Create Date: 2026-09-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f82d6a11b3c'
down_revision: Union[str, None] = '3414e9c24e2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- native Postgres enum type ---
    op.execute("CREATE TYPE recommendation_feedback_action AS ENUM ('ACCEPTED', 'DISMISSED', 'DEFERRED')")

    # --- recommendation_feedback table ---
    op.create_table(
        'recommendation_feedback',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('recommendation_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.Enum('ACCEPTED', 'DISMISSED', 'DEFERRED', name='recommendation_feedback_action'), nullable=False),
        sa.Column('suggested_task_id', sa.UUID(), nullable=True),
        sa.Column('feedback_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['suggested_task_id'], ['tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- indices ---
    op.create_index(op.f('ix_recommendation_feedback_user_id'), 'recommendation_feedback', ['user_id'], unique=False)
    op.create_index(op.f('ix_recommendation_feedback_recommendation_id'), 'recommendation_feedback', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_recommendation_feedback_action'), 'recommendation_feedback', ['action'], unique=False)
    op.create_index(op.f('ix_recommendation_feedback_suggested_task_id'), 'recommendation_feedback', ['suggested_task_id'], unique=False)


def downgrade() -> None:
    # --- drop indices ---
    op.drop_index(op.f('ix_recommendation_feedback_suggested_task_id'), table_name='recommendation_feedback')
    op.drop_index(op.f('ix_recommendation_feedback_action'), table_name='recommendation_feedback')
    op.drop_index(op.f('ix_recommendation_feedback_recommendation_id'), table_name='recommendation_feedback')
    op.drop_index(op.f('ix_recommendation_feedback_user_id'), table_name='recommendation_feedback')

    # --- drop table ---
    op.drop_table('recommendation_feedback')

    # --- drop enum type ---
    op.execute("DROP TYPE recommendation_feedback_action")
