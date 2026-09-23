"""create_farmer_crops_table

Revision ID: 1c41e2dc0718
Revises: c917bfafa29c
Create Date: 2026-09-23 15:48:41.232571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1c41e2dc0718'
down_revision: Union[str, Sequence[str], None] = 'c917bfafa29c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create farmer_crops table linking farmers and their cultivated crops."""
    op.create_table(
        'farmer_crops',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('crop_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('area_acres', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='farmer_crops_pkey'),
        sa.ForeignKeyConstraint(['farmer_id'], ['user_profiles.id'], name='farmer_crops_farmer_id_fkey', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], name='farmer_crops_crop_id_fkey', ondelete='RESTRICT'),
        sa.UniqueConstraint('farmer_id', 'crop_id', name='uq_farmer_crops_farmer_crop'),
        sa.CheckConstraint('area_acres >= 0', name='ck_farmer_crops_area_acres_non_negative')
    )
    op.create_index(op.f('ix_farmer_crops_farmer_id'), 'farmer_crops', ['farmer_id'], unique=False)
    op.create_index(op.f('ix_farmer_crops_crop_id'), 'farmer_crops', ['crop_id'], unique=False)


def downgrade() -> None:
    """Drop farmer_crops table and indexes."""
    op.drop_index(op.f('ix_farmer_crops_crop_id'), table_name='farmer_crops')
    op.drop_index(op.f('ix_farmer_crops_farmer_id'), table_name='farmer_crops')
    op.drop_table('farmer_crops')
