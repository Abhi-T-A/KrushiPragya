"""create_user_profiles_table

Revision ID: 551865bd2180
Revises: 917bd8d97856
Create Date: 2026-09-23 14:56:22.782562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '551865bd2180'
down_revision: Union[str, Sequence[str], None] = '917bd8d97856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create user_profiles table linking auth.users and villages."""
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('village_id', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=5), server_default='kn', nullable=False),
        sa.Column('land_holding_acres', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['auth.users.id'], name='user_profiles_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['village_id'], ['villages.id'], name='user_profiles_village_id_fkey', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='user_profiles_pkey')
    )
    op.create_index(op.f('ix_user_profiles_village_id'), 'user_profiles', ['village_id'], unique=False)


def downgrade() -> None:
    """Drop user_profiles table."""
    op.drop_index(op.f('ix_user_profiles_village_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
