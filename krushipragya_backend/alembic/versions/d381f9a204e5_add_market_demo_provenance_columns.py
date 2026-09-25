"""add_market_demo_provenance_columns

Revision ID: d381f9a204e5
Revises: c194e82a03d1
Create Date: 2026-09-26 02:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd381f9a204e5'
down_revision: Union[str, Sequence[str], None] = 'c194e82a03d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Update market_data_sources table
    src_cols = [c['name'] for c in inspector.get_columns('market_data_sources')]
    if 'is_demo' not in src_cols:
        op.add_column('market_data_sources', sa.Column('is_demo', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    if 'data_mode' not in src_cols:
        op.add_column('market_data_sources', sa.Column('data_mode', sa.String(length=20), server_default='LIVE', nullable=False))

    # 2. Update market_price_records table
    price_cols = [c['name'] for c in inspector.get_columns('market_price_records')]
    if 'is_seeded' not in price_cols:
        op.add_column('market_price_records', sa.Column('is_seeded', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    if 'data_mode' not in price_cols:
        op.add_column('market_price_records', sa.Column('data_mode', sa.String(length=20), server_default='DEMO_SEEDED', nullable=False))

    # 3. Mark seeded source and benchmark price records for hackathon demo
    conn.execute(sa.text("""
        UPDATE market_data_sources
        SET is_demo = true,
            data_mode = 'DEMO_SEEDED',
            source_type = 'DEMO_SEEDED',
            sync_status = 'SEEDED_DEMO',
            name = 'Demo Benchmark Mandi Rates (Hackathon Demo Seed)'
        WHERE code = 'OGD_INDIA'
    """))

    conn.execute(sa.text("""
        UPDATE market_price_records
        SET is_seeded = true,
            data_mode = 'DEMO_SEEDED'
    """))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Revert metadata changes
    conn.execute(sa.text("""
        UPDATE market_data_sources
        SET is_demo = false,
            data_mode = 'LIVE',
            source_type = 'GOVERNMENT_OGD',
            sync_status = 'IDLE',
            name = 'Open Government Data (OGD) Platform India - DMI'
        WHERE code = 'OGD_INDIA'
    """))

    # 2. Drop columns if present
    price_cols = [c['name'] for c in inspector.get_columns('market_price_records')]
    if 'data_mode' in price_cols:
        op.drop_column('market_price_records', 'data_mode')
    if 'is_seeded' in price_cols:
        op.drop_column('market_price_records', 'is_seeded')

    src_cols = [c['name'] for c in inspector.get_columns('market_data_sources')]
    if 'data_mode' in src_cols:
        op.drop_column('market_data_sources', 'data_mode')
    if 'is_demo' in src_cols:
        op.drop_column('market_data_sources', 'is_demo')
