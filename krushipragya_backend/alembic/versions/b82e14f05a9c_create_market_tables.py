"""create_market_tables

Revision ID: b82e14f05a9c
Revises: 4c187068455c
Create Date: 2026-09-25 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b82e14f05a9c'
down_revision: Union[str, Sequence[str], None] = '4c187068455c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. market_data_sources
    op.create_table(
        'market_data_sources',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=50), server_default='GOVERNMENT_OGD', nullable=False),
        sa.Column('base_url', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(length=50), server_default='IDLE', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index(op.f('ix_market_data_sources_code'), 'market_data_sources', ['code'], unique=True)

    # 2. markets
    op.create_table(
        'markets',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=False),
        sa.Column('taluk', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index(op.f('ix_markets_code'), 'markets', ['code'], unique=True)
    op.create_index(op.f('ix_markets_name'), 'markets', ['name'], unique=False)
    op.create_index('ix_markets_state_district', 'markets', ['state', 'district'], unique=False)
    op.create_index('ix_markets_coordinates', 'markets', ['latitude', 'longitude'], unique=False)

    # 3. market_crop_mappings
    op.create_table(
        'market_crop_mappings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('crop_id', sa.UUID(), nullable=False),
        sa.Column('canonical_crop_code', sa.String(length=50), nullable=False),
        sa.Column('raw_commodity_name', sa.String(length=100), nullable=False),
        sa.Column('variety', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_commodity_name', 'variety', name='uq_market_crop_mapping_raw_variety'),
    )
    op.create_index(op.f('ix_market_crop_mappings_crop_id'), 'market_crop_mappings', ['crop_id'], unique=False)

    # 4. market_price_records
    op.create_table(
        'market_price_records',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('market_id', sa.UUID(), nullable=False),
        sa.Column('crop_id', sa.UUID(), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=True),
        sa.Column('source_record_id', sa.String(length=150), nullable=True),
        sa.Column('arrival_date', sa.Date(), nullable=False),
        sa.Column('commodity_raw', sa.String(length=100), nullable=False),
        sa.Column('variety', sa.String(length=100), server_default='Standard', nullable=False),
        sa.Column('grade', sa.String(length=50), server_default='FAQ', nullable=False),
        sa.Column('min_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('max_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('modal_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('arrival_quantity', sa.Numeric(precision=12, scale=2), server_default='0.0', nullable=False),
        sa.Column('unit', sa.String(length=20), server_default='Quintal', nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['crop_id'], ['crops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['market_data_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('market_id', 'crop_id', 'arrival_date', 'variety', 'grade', name='uq_market_price_unique_arrival'),
    )
    op.create_index(op.f('ix_market_price_records_market_id'), 'market_price_records', ['market_id'], unique=False)
    op.create_index(op.f('ix_market_price_records_crop_id'), 'market_price_records', ['crop_id'], unique=False)
    op.create_index(op.f('ix_market_price_records_source_id'), 'market_price_records', ['source_id'], unique=False)
    op.create_index(op.f('ix_market_price_records_arrival_date'), 'market_price_records', ['arrival_date'], unique=False)
    op.create_index('ix_market_prices_crop_date', 'market_price_records', ['crop_id', 'arrival_date'], unique=False)
    op.create_index('ix_market_prices_market_date', 'market_price_records', ['market_id', 'arrival_date'], unique=False)

    # 5. farmer_market_follows
    op.create_table(
        'farmer_market_follows',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('farmer_id', sa.UUID(), nullable=False),
        sa.Column('market_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['farmer_id'], ['user_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('farmer_id', 'market_id', name='uq_farmer_market_follow'),
    )
    op.create_index(op.f('ix_farmer_market_follows_farmer_id'), 'farmer_market_follows', ['farmer_id'], unique=False)


def downgrade() -> None:
    op.drop_table('farmer_market_follows')
    op.drop_table('market_price_records')
    op.drop_table('market_crop_mappings')
    op.drop_table('markets')
    op.drop_table('market_data_sources')
