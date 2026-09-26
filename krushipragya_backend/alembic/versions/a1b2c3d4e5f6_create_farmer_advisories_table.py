"""create_farmer_advisories_table

Revision ID: a1b2c3d4e5f6
Revises: f5a6b7c8d9e0
Create Date: 2026-09-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely create farmer_advisories table
    op.create_table(
        'farmer_advisories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('farmer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('crop_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('farmer_crops.id', ondelete='SET NULL'), nullable=True),
        sa.Column('crop_code', sa.String(length=50), nullable=False),
        sa.Column('village_id', sa.String(length=50), nullable=True),
        sa.Column('risk_level', sa.String(length=20), nullable=False, server_default='INFO'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('title_kn', sa.String(length=255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('summary_kn', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('recommended_actions', sa.JSON(), nullable=False),
        sa.Column('structured_actions', sa.JSON(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('confidence_level', sa.String(length=20), nullable=False, server_default='HIGH'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('fingerprint', sa.String(length=64), nullable=True),
        sa.Column('is_llm_generated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('weather_observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_index('ix_farmer_advisories_farmer_id', 'farmer_advisories', ['farmer_id'])
    op.create_index('ix_farmer_advisories_crop_id', 'farmer_advisories', ['crop_id'])
    op.create_index('ix_farmer_advisories_crop_code', 'farmer_advisories', ['crop_code'])
    op.create_index('ix_farmer_advisories_village_id', 'farmer_advisories', ['village_id'])
    op.create_index('ix_farmer_advisories_status', 'farmer_advisories', ['status'])
    op.create_index('ix_farmer_advisories_fingerprint', 'farmer_advisories', ['fingerprint'])
    op.create_index('ix_farmer_advisories_valid_until', 'farmer_advisories', ['valid_until'])
    op.create_index('ix_farmer_advisories_farmer_status', 'farmer_advisories', ['farmer_id', 'status'])
    op.create_index('ix_farmer_advisories_crop_status', 'farmer_advisories', ['crop_code', 'status'])


def downgrade() -> None:
    op.drop_index('ix_farmer_advisories_crop_status', table_name='farmer_advisories')
    op.drop_index('ix_farmer_advisories_farmer_status', table_name='farmer_advisories')
    op.drop_index('ix_farmer_advisories_valid_until', table_name='farmer_advisories')
    op.drop_index('ix_farmer_advisories_fingerprint', table_name='farmer_advisories')
    op.drop_index('ix_farmer_advisories_status', table_name='farmer_advisories')
    op.drop_index('ix_farmer_advisories_village_id', table_name='farmer_advisories')
    op.drop_index('ix_farmer_advisories_crop_code', table_name='farmer_advisories')
    op.drop_index('ix_farmer_advisories_crop_id', table_name='farmer_advisories')
    op.drop_index('ix_farmer_advisories_farmer_id', table_name='farmer_advisories')
    op.drop_table('farmer_advisories')
